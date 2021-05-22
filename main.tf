module "github_webhook_request_validator" {
  source = "./modules//dynamic-github-source"

  github_token_ssm_value = var.github_token_ssm_value
  codebuild_name         = var.codebuild_name
  codebuild_buildspec    = var.codebuild_buildspec
  codebuild_environment  = var.codebuild_environment
  repos                  = var.repos
}