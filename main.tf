locals {
  repos = [for repo in var.repos : merge(repo, {
    filter_groups = [for filter_group in repo.filter_groups :
      defaults(filter_group, {
        exclude_matched_filter = false
      })
    ]
  })]
  lambda_deps_zip_path     = "${path.module}/lambda_deps.zip"
  lambda_deps_requirements = "PyGithub==1.54.1 jsonpath-ng==1.5.3"
}

module "lambda" {
  source           = "github.com/marshall7m/terraform-aws-lambda?ref=v0.1.6"
  filename         = data.archive_file.lambda_function.output_path
  source_code_hash = data.archive_file.lambda_function.output_base64sha256
  function_name    = var.function_name
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.8"
  allowed_to_invoke = [
    {
      statement_id = "APIGatewayInvokeAccess"
      principal    = "apigateway.amazonaws.com"
      arn          = "${local.execution_arn}/*/*"
    }
  ]
  destination_config = var.lambda_destination_config
  enable_cw_logs     = true
  env_vars = merge({
    GITHUB_WEBHOOK_SECRET_SSM_KEY = var.github_secret_ssm_key
  }, var.includes_private_repo ? { GITHUB_TOKEN_SSM_KEY = var.github_token_ssm_key } : {})
  custom_role_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    aws_iam_policy.lambda.arn
  ]
  force_detach_policies = true
  lambda_layers = [
    {
      filename         = data.archive_file.lambda_deps.output_path
      name             = "${var.function_name}-deps"
      runtimes         = ["python3.8"]
      source_code_hash = data.archive_file.lambda_deps.output_base64sha256
      description      = "Dependencies for lambda function: ${var.function_name}"
    }
  ]
}



resource "null_resource" "lambda_pip_deps" {
  triggers = {
    requirements_hash = base64sha256(local.lambda_deps_requirements)
    # use zip file hash as a trigger so the command is executed even when
    # `terraform init -upgrade` removes the zip file on new installation of terraform module
    zip_hash = fileexists(local.lambda_deps_zip_path) ? 0 : timestamp()
  }
  provisioner "local-exec" {
    # pip install runtime packages needed for function
    command = <<EOF
    pip install --upgrade --target ${path.module}/deps/python ${local.lambda_deps_requirements}
    EOF
  }
}

#using lambda layer file for filter groups given lambda functions have a size limit of 4KB for env vars and easier parsing
resource "local_file" "filter_groups" {
  content  = jsonencode({ for repo in local.repos : repo.name => repo.filter_groups })
  filename = "${path.module}/deps/filter_groups.json"
}

data "archive_file" "lambda_deps" {
  type        = "zip"
  source_dir  = "${path.module}/deps"
  output_path = local.lambda_deps_zip_path
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

data "aws_kms_key" "ssm" {
  key_id = "alias/aws/ssm"
}

data "aws_iam_policy_document" "lambda" {

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
    for_each = var.includes_private_repo ? [1] : []
    content {
      sid    = "GithubWebhookTokenReadAccess"
      effect = "Allow"
      actions = [
        "ssm:GetParameter"
      ]
      resources = [try(aws_ssm_parameter.github_token[0].arn, data.aws_ssm_parameter.github_token[0].arn)]
    }
  }
}

resource "aws_iam_policy" "lambda" {
  name   = var.function_name
  policy = data.aws_iam_policy_document.lambda.json
}

resource "github_repository_webhook" "this" {
  count      = length(local.repos)
  repository = local.repos[count.index].name

  configuration {
    url          = "${aws_api_gateway_deployment.this.invoke_url}${aws_api_gateway_stage.this.stage_name}${aws_api_gateway_resource.this.path}"
    content_type = "json"
    insecure_ssl = false
    secret       = random_password.github_webhook_secret.result
  }

  active = true
  #pulls distinct filter group events
  events = distinct(flatten([for group in local.repos[count.index].filter_groups : [for filter in group :
  filter.pattern if filter.type == "event" && filter.exclude_matched_filter != true]]))
}

resource "aws_ssm_parameter" "github_token" {
  count       = var.includes_private_repo && var.github_token_ssm_value != "" ? 1 : 0
  name        = var.github_token_ssm_key
  description = var.github_token_ssm_description
  type        = "SecureString"
  value       = var.github_token_ssm_value
  tags        = var.github_token_ssm_tags
}

data "aws_ssm_parameter" "github_token" {
  count = var.includes_private_repo && var.github_token_ssm_value == "" ? 1 : 0
  name  = var.github_token_ssm_key
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