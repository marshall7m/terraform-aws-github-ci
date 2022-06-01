output "invoke_url" {
  value = module.mut_github_webhook_request_validator.github_webhook_invoke_url
}

output "lambda_log_group_name" {
  value = module.mut_github_webhook_request_validator.lambda_log_group_name
}

output "function_name" {
  value = module.mut_github_webhook_request_validator.function_name
}

output "agw_log_group_name" {
  value = try(module.mut_github_webhook_request_validator.agw_log_group_name, null)
}

output "webhook_urls" {
  description = "Map of repo webhook URLs"
  value       = module.mut_github_webhook_request_validator.webhook_urls
  sensitive   = true
}