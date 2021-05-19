output "api_invoke_url" {
  value = module.github_webhook_request_validator.invoke_url
}

output "request_validator_function_arn" {
  value = module.github_webhook_request_validator.function_arn
}

output "payload_validator_function_arn" {
  value = module.lambda.function_arn
}

output "codebuild_arn" {
  value = module.codebuild.arn
}