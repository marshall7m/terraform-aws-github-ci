output "api_invoke_url" {
  value = module.dynamic_github_source.invoke_url
}

output "request_validator_function_arn" {
  value = module.dynamic_github_source.function_arn
}

output "payload_filter_function_arn" {
  value = module.dynamic_github_source.module.lambda.function_arn
}

output "codebuild_arn" {
  value = module.dynamic_github_source.module.codebuild.arn
}

output "repo_cfg" {
  value = module.dynamic_github_source.local.repos
}