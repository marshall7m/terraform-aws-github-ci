locals {
  lambda_destination_arns = concat(var.lambda_success_destination_arns, var.lambda_failure_destination_arns)
}

resource "aws_lambda_function_event_invoke_config" "lambda" {
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
  }
  custom_role_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    aws_iam_policy.lambda.arn
  ]
}

data "aws_arn" "lambda_dest" {
  count = length(local.lambda_destination_arns)
  arn   = local.lambda_destination_arns[count.index]
}

data "aws_iam_policy_document" "lambda" {
  statement {
    sid    = "GithubWebhookSecretReadAccess"
    effect = "Allow"
    actions = [
      "ssm:GetParameter"
    ]
    resources = [aws_ssm_parameter.github_secret.arn]
  }

  dynamic "statement" {
    for_each = contains(data.aws_arn.lambda_dest[*].service, "sqs") ? [1] : []
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
    for_each = contains(data.aws_arn.lambda_dest[*].service, "sns") ? [1] : []
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
    for_each = contains(data.aws_arn.lambda_dest[*].service, "events") ? [1] : []
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
    for_each = contains(data.aws_arn.lambda_dest[*].service, "lambda") ? [1] : []
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

data "archive_file" "lambda_function" {
  type        = "zip"
  source_dir  = "${path.module}/function"
  output_path = "${path.module}/function.zip"
}

resource "github_repository_webhook" "this" {
  count      = length(var.repos)
  repository = var.repos[count.index].name

  configuration {
    url          = "${aws_api_gateway_deployment.this.invoke_url}${aws_api_gateway_stage.this.stage_name}${aws_api_gateway_resource.this.path}"
    content_type = "json"
    insecure_ssl = false
    secret       = random_password.github_webhook_secret.result
  }

  active = true
  events = var.repos[count.index].events
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