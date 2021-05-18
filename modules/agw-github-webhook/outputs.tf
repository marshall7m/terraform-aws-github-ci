output "invoke_url" {
  description = "API invoke URL the github webhook will ping"
  value       = "${aws_api_gateway_deployment.this.invoke_url}${aws_api_gateway_stage.this.stage_name}${aws_api_gateway_resource.this.path}"
}

output "function_arn" {
  description = "ARN of AWS Lambda function used to validate Github webhook request"
  value       = module.lambda.function_arn
}