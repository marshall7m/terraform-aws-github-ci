locals {
  mut_id        = "mut-${random_string.mut.id}"
  function_name = "${local.mut_id}-github-webhook-validator"
}

resource "random_string" "mut" {
  length  = 8
  lower   = true
  upper   = false
  special = false
}

module "mut_github_webhook_request_validator" {
  source                 = "../../..//"
  create_api             = true
  repos                  = var.repos
  includes_private_repo  = var.includes_private_repo
  github_token_ssm_value = var.github_token_ssm_value
  github_token_ssm_key   = "${local.function_name}-token"
  function_name          = local.function_name
}