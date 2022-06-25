module "mut_github_webhook_request_validator" {
  source             = "../../../../..//"
  create_api         = true
  enable_api_cw_logs = false
  repos = [
    {
      name = "user/test-repo"
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