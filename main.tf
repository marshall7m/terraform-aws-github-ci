locals {
  repos = [for repo in var.repos : merge(repo, {
    filter_groups = [for filter_group in repo.filter_groups :
      defaults(filter_group, {
        exclude_matched_filter = false
      })
    ]
  })]
  private_repos = [for repo in local.repos : defaults(
    repo, {
      create_github_token_ssm_param = true
      github_token_ssm_key          = repo.create_github_token_ssm_param ? "${var.function_name}-${repo.name}-gh-token" : null
    }
  ) if repo.is_private == true]

  github_secret_ssm_key = coalesce(var.github_secret_ssm_key, "${var.function_name}-secret")

  create_ssm_params   = [for repo in local.private_repos : repo if repo.create_github_token_ssm_param == true]
  load_ssm_param_arns = [for repo in local.private_repos : repo.github_token_ssm_param_arn if repo.create_github_token_ssm_param == false && repo.github_token_ssm_param_arn != null]
  load_ssm_param_keys = [for repo in local.private_repos : repo.github_token_ssm_key if repo.create_github_token_ssm_param == false && repo.github_token_ssm_key != null]
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

  dynamic "statement" {
    for_each = length(local.private_repos) > 0 ? [1] : []
    content {
      sid       = "SSMDecryptAccess"
      effect    = "Allow"
      actions   = ["kms:Decrypt"]
      resources = [data.aws_kms_key.ssm.arn]
    }
  }

  dynamic "statement" {
    for_each = length(local.private_repos) > 0 ? [1] : []
    content {
      sid    = "GithubWebhookTokenReadAccess"
      effect = "Allow"
      actions = [
        "ssm:GetParameter"
      ]
      resources = concat(local.load_ssm_param_arns, try(aws_ssm_parameter.github_token[*].arn, []), try(data.aws_ssm_parameter.github_token[*].arn, []))
    }
  }
}

resource "aws_iam_policy" "lambda" {
  name   = var.function_name
  policy = data.aws_iam_policy_document.lambda.json
}

# using file for filter groups given lambda functions have a size limit of 4KB for env vars
resource "local_file" "filter_groups" {
  content  = jsonencode({ for repo in local.repos : repo.name => repo.filter_groups })
  filename = "${path.module}/function/filter_groups.json"
}

module "lambda_function" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "3.3.1"

  function_name = var.function_name
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"

  source_path = "${path.module}/function"

  # put repo github ssm key mapping within env vars rather than the Lambda function deployment
  # since the latter involves creating a new deployment when the token(s) need to be refreshed
  environment_variables = {
    GITHUB_WEBHOOK_SECRET_SSM_KEY = local.github_secret_ssm_key
    TOKEN_SSM_KEYS = jsonencode({
      for repo in local.private_repos : repo.name => coalesce(
        try(split(":parameter", repo.github_token_ssm_param_arn)[1], null),
        repo.github_token_ssm_key
      )
    })
  }

  publish = true
  allowed_triggers = {
    APIGatewayInvokeAccess = {
      service    = "apigateway"
      source_arn = "${local.execution_arn}/*/*"
    }
  }
  policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    aws_iam_policy.lambda.arn
  ]
  attach_policies               = true
  number_of_policies            = 2
  role_force_detach_policies    = true
  attach_cloudwatch_logs_policy = true

  destination_on_success = var.lambda_destination_on_success
  destination_on_failure = var.lambda_destination_on_failure

  vpc_subnet_ids         = var.lambda_vpc_subnet_ids
  vpc_security_group_ids = var.lambda_vpc_security_group_ids
  attach_network_policy  = var.lambda_vpc_attach_network_policy

  depends_on = [
    local_file.filter_groups
  ]
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
  count       = length(local.create_ssm_params)
  name        = local.create_ssm_params[count.index].github_token_ssm_key
  description = "GitHub token used for accessing the private repo within ${var.function_name}"
  type        = "SecureString"
  value       = local.create_ssm_params[count.index].github_token_ssm_value
  tags        = local.create_ssm_params[count.index].github_token_ssm_tags
}

data "aws_ssm_parameter" "github_token" {
  count = length(local.load_ssm_param_keys)
  name  = local.load_ssm_param_keys[count.index]
}

resource "aws_ssm_parameter" "github_secret" {
  name        = local.github_secret_ssm_key
  description = var.github_secret_ssm_description
  type        = "SecureString"
  value       = random_password.github_webhook_secret.result
  tags        = var.github_secret_ssm_tags
}

resource "random_password" "github_webhook_secret" {
  length = 24
}