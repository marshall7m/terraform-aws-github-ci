output "api_invoke_url" {
  description = "API invoke URL the github webhook will ping"
  value       = module.dynamic_github_source.api_invoke_url
}

output "request_validator_function_arn" {
  description = "ARN of the Lambda function that validates the Github request"
  value       = module.dynamic_github_source.request_validator_function_arn
}

output "payload_validator_function_arn" {
  description = "ARN of the Lambda function that validates the Github payload"
  value       = module.dynamic_github_source.payload_validator_function_arn
}

output "codebuild_arn" {
  description = "ARN of the CodeBuild project will be conditionally triggered from the payload validator function"
  value       = module.dynamic_github_source.codebuild_arn
}