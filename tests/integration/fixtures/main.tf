module "mut_github_webhook_request_validator" {
  source                 = "../../..//"
  create_api             = true
  repos                  = var.repos
  includes_private_repo  = var.includes_private_repo
  github_token_ssm_value = var.github_token_ssm_value
}