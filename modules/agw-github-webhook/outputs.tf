output "invoke_url" {
  description = "API invoke URL the github webhook will ping"
  value       = "${aws_api_gateway_deployment.this.invoke_url}${aws_api_gateway_stage.this.stage_name}${aws_api_gateway_resource.this.path}"
}

output "function_name" {
  description = "Name of AWS Lambda function used to validate Github webhook"
  value       = local.function_name
}

output "function_arn" {
  description = "ARN of AWS Lambda function used to validate Github webhook"
  value       = module.lambda.function_arn
}

output "github_secret_ssm_key" {
  description = "Key name for Github secret store in AWS SSM Parameter Store"
  value       = local.github_secret_ssm_key
}

output "api_name" {
  description = "Name of AWS API gateway REST API"
  value       = local.api_name
}