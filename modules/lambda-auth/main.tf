locals {
  default_repos = [for repo in var.repos : merge(repo, {
    filter_groups = [for filter_group in repo.filter_groups :
      defaults(filter_group, {
        exclude_matched_filter = false
      })
    ]
  })]
  repos = [for repo in local.default_repos : merge(repo, {
    #pulls distinct filter group events to define the Github webhook events
    events = distinct(flatten([for filter_group in repo.filter_groups :
    filter_group.events if filter_group.exclude_matched_filter != true]))
  })]
  lambda_destination_arns = concat(var.lambda_success_destination_arns, var.lambda_failure_destination_arns)
}

resource "aws_lambda_function_event_invoke_config" "lambda" {
  count         = length(local.lambda_destination_arns) > 0 ? 1 : 0
  function_name = module.lambda.function_name
  destination_config {
    dynamic "on_success" {
      for_each = toset(var.lambda_success_destination_arns)
      content {
        destination = on_success.value
      }
    }

    dynamic "on_failure" {
      for_each = toset(var.lambda_failure_destination_arns)
      content {
        destination = on_failure.value
      }
    }
  }
}

module "lambda" {
  source           = "github.com/marshall7m/terraform-aws-lambda"
  filename         = data.archive_file.lambda_function.output_path
  source_code_hash = data.archive_file.lambda_function.output_base64sha256
  function_name    = var.function_name
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.8"
  allowed_to_invoke = [
    {
      statement_id = "APIGatewayInvokeAccess"
      principal    = "apigateway.amazonaws.com"
      arn          = "${aws_api_gateway_rest_api.this.execution_arn}/*/*"
    }
  ]
  enable_cw_logs = true
  env_vars = {
    GITHUB_WEBHOOK_SECRET_SSM_KEY = var.github_secret_ssm_key
    GITHUB_TOKEN_SSM_KEY          = var.github_token_ssm_key
  }
  custom_role_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    aws_iam_policy.lambda.arn
  ]
  lambda_layers = [
    {
      filename         = data.archive_file.lambda_deps.output_path
      name             = "${var.function_name}-deps"
      runtimes         = ["python3.8"]
      source_code_hash = data.archive_file.lambda_deps.output_base64sha256
      description      = "Dependencies for lambda function: ${var.function_name}"
    }
  ]
  # depends_on = [
  #   archive_file.lambda_function
  # ]
}


# pip install runtime packages needed for function
resource "null_resource" "lambda_pip_deps" {
  triggers = {
    zip_hash = fileexists("${path.module}/lambda_deps.zip") ? 0 : timestamp()
  }
  provisioner "local-exec" {
    command = <<EOF
    pip install --target ${path.module}/deps/python PyGithub==1.54.1
    EOF
  }
}

data "archive_file" "lambda_deps" {
  type        = "zip"
  source_dir  = "${path.module}/deps"
  output_path = "${path.module}/lambda_deps.zip"
  depends_on = [
    local_file.filter_groups,
    null_resource.lambda_pip_deps
  ]
}

data "archive_file" "lambda_function" {
  type        = "zip"
  source_dir  = "${path.module}/function"
  output_path = "${path.module}/function.zip"
}

#using lambda layer file for filter groups given lambda functions have a size limit of 4KB for env vars and easier parsing
resource "local_file" "filter_groups" {
  content  = jsonencode({ for repo in local.repos : repo.name => repo.filter_groups })
  filename = "${path.module}/deps/filter_groups.json"
}

data "aws_arn" "lambda_dest" {
  count = length(local.lambda_destination_arns)
  arn   = local.lambda_destination_arns[count.index]
}

data "aws_kms_key" "ssm" {
  key_id = "alias/aws/ssm"
}

resource "aws_ssm_parameter" "github_token" {
  count       = var.create_github_token_ssm_param && var.github_token_ssm_value != "" ? 1 : 0
  name        = var.github_token_ssm_key
  description = var.github_token_ssm_description
  type        = "SecureString"
  value       = var.github_token_ssm_value
  tags        = var.github_token_ssm_tags
}

data "aws_ssm_parameter" "github_token" {
  count = var.create_github_token_ssm_param == false && var.github_token_ssm_value == "" ? 1 : 0
  name  = var.github_token_ssm_key
}

data "aws_iam_policy_document" "lambda" {

  statement {
    sid    = "GithubWebhookTokenReadAccess"
    effect = "Allow"
    actions = [
      "ssm:GetParameter"
    ]
    resources = [try(aws_ssm_parameter.github_token[0].arn, data.aws_ssm_parameter.github_token[0].arn)]
  }

  statement {
    sid       = "GithubWebhookSecretReadAccess"
    effect    = "Allow"
    actions   = ["ssm:GetParameter"]
    resources = [aws_ssm_parameter.github_secret.arn]
  }

  statement {
    sid       = "SSMDecryptAccess"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = [data.aws_kms_key.ssm.arn]
  }

  dynamic "statement" {
    for_each = contains(try(data.aws_arn.lambda_dest[*].service, []), "sqs") ? [1] : []
    content {
      sid    = "InvokeSqsDestination"
      effect = "Allow"
      actions = [
        "sqs:SendMessage"
      ]
      resources = [for entity in data.aws_arn.lambda_dest : entity.arn if entity.service == "sqs"]
    }
  }

  dynamic "statement" {
    for_each = contains(try(data.aws_arn.lambda_dest[*].service, []), "sns") ? [1] : []
    content {
      sid    = "InvokeSnsDestination"
      effect = "Allow"
      actions = [
        "sns:Publish"
      ]
      resources = [for entity in data.aws_arn.lambda_dest : entity.arn if entity.service == "sns"]
    }
  }

  dynamic "statement" {
    for_each = contains(try(data.aws_arn.lambda_dest[*].service, []), "events") ? [1] : []
    content {
      sid    = "InvokeEventsDestination"
      effect = "Allow"
      actions = [
        "events:PutEvents"
      ]
      resources = [for entity in data.aws_arn.lambda_dest : entity.arn if entity.service == "events"]
    }
  }

  dynamic "statement" {
    for_each = contains(try(data.aws_arn.lambda_dest[*].service, []), "lambda") ? [1] : []
    content {
      sid    = "InvokeLambdaDestination"
      effect = "Allow"
      actions = [
        "lambda:InvokeFunction"
      ]
      resources = [for entity in data.aws_arn.lambda_dest : entity.arn if entity.service == "lambda"]
    }
  }
}

resource "aws_iam_policy" "lambda" {
  name   = var.function_name
  policy = data.aws_iam_policy_document.lambda.json
}

resource "github_repository_webhook" "this" {
  for_each   = { for repo in local.repos : repo.name => repo }
  repository = each.value.name

  configuration {
    url          = "${aws_api_gateway_deployment.this.invoke_url}${aws_api_gateway_stage.this.stage_name}${aws_api_gateway_resource.this.path}"
    content_type = "json"
    insecure_ssl = false
    secret       = random_password.github_webhook_secret.result
  }

  active = true
  events = each.value.events
}

resource "aws_ssm_parameter" "github_secret" {
  name        = var.github_secret_ssm_key
  description = var.github_secret_ssm_description
  type        = "SecureString"
  value       = random_password.github_webhook_secret.result
  tags        = var.github_secret_ssm_tags
}

resource "random_password" "github_webhook_secret" {
  length = 24
}