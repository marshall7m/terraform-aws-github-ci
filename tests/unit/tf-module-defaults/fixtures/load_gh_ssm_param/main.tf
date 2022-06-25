resource "aws_ssm_parameter" "this" {
  name  = "bar"
  value = "foo"
  type  = "String"
}

module "mut_github_webhook_request_validator" {
  source     = "../../../../..//"
  create_api = true
  repos = [
    {
      name                          = "user/test-repo-a"
      is_private                    = true
      create_github_token_ssm_param = false
      github_token_ssm_param_arn    = aws_ssm_parameter.this.arn
      filter_groups = [
        [
          {
            type    = "event"
            pattern = "push"
          }
        ]
      ]
    },
    {
      name                          = "user/test-repo-b"
      is_private                    = true
      create_github_token_ssm_param = false
      github_token_ssm_key          = var.dummy_ssm_key
      filter_groups = [
        [
          {
            type    = "event"
            pattern = "push"
          }
        ]
      ]
    }
  ]
}

variable "dummy_ssm_key" {
  description = "Key for a pre-existing dummy AWS SSM parameter"
  type        = string
}