output "invoke_url" {
  description = "API invoke URL the github webhook will ping"
  value       = "${aws_api_gateway_deployment.this.invoke_url}${aws_api_gateway_stage.this.stage_name}${aws_api_gateway_resource.this.path}"
}

output "webhook_urls" {
  description = "Map of repo webhook URLs"
  value       = { for repo in github_repository_webhook.this : repo.repository => repo.url }
  sensitive   = true
}

output "function_arn" {
  description = "ARN of AWS Lambda function used to validate Github webhook request"
  value       = module.lambda.function_arn
}

output "function_name" {
  description = "Name of the Lambda function used to validate Github webhook request"
  value       = module.lambda.function_name
}

output "cw_log_group_arn" {
  description = "ARN of the CloudWatch log group associated with the Lambda function"
  value       = one([module.lambda.cw_log_group_arn])
}

output "lambda_deps" {
  description = "Package depedency's file configurations for the Lambda function"
  value       = data.archive_file.lambda_deps
}

output "github_token_ssm_arn" {
  description = "ARN of the AWS System Manager Parameter Store key used for the sensitive GitHub Token"
  value       = var.create_github_token_ssm_param == true ? aws_ssm_parameter.github_token[0].arn : data.aws_ssm_parameter.github_token[0].arn
}