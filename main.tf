module "dynamic_github_source" {
  source = "./modules//dynamic-github-source"

  create_github_secret_ssm_param = true
  github_secret_ssm_value        = var.github_secret_ssm_value
  github_token_ssm_value         = var.github_token
  codebuild_name                 = var.codebuild_name
  codebuild_buildspec            = var.codebuild_buildspec
  codebuild_environment          = var.codebuild_environment
  repos                          = var.repos
}