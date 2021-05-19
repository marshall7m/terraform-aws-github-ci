terraform {
  required_version = ">=0.14.8"
  experiments      = [module_variable_optional_attrs]
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 3.22"
    }
    github = {
      source  = "integrations/github"
      version = ">=4.4.0"
    }
  }
}

provider "github" {
  owner = "marshall7m"
}

variable "named_repos" {
  description = "List of GitHub repositories to create webhooks for"
  type = list(object({
    name   = string
    events = list(string)
    active = bool
  }))
  default = [{
    name   = "terraform-aws-iam"
    events = ["push"]
    active = true
  }]
}

variable "queried_repos" {
  description = "List of queries to match repositories used for creating github webhooks. See for query syntax: https://docs.github.com/en/github/searching-for-information-on-github/understanding-the-search-syntax"
  type = list(object({
    query  = string
    events = list(string)
    active = bool
  }))
  default = [{
    query  = "aws in:name"
    events = ["push"]
    active = true
  }]
}

locals {
  queried_repos = [for group in var.queried_repos :
    defaults(length(regexall("user:.+", group.query)) == 0 ?
      merge(group, { query = "${group.query} user:${data.github_user.current.login}" }) : group,
    { active = true })
  ]
  # queried_repos_final = distinct(flatten([for i in range(length(local.queried_repos)) :
  #   values({ for repo in data.github_repositories.queried[i].names :
  #     repo => merge({ name = repo }, local.queried_repos[i])
  #   if contains(local.named_repos[*].name, repo) == false })
  # ]))
  queried_repos_final = distinct(flatten([for i in range(length(local.queried_repos)) :
    [for repo in data.github_repositories.queried[i].names :
      merge({ name = repo }, local.queried_repos[i])
    if contains(var.named_repos[*].name, repo) == false]
  ]))
  all_repos = concat(var.named_repos, local.queried_repos_final)
}

data "github_repositories" "queried" {
  count = length(local.queried_repos)
  query = local.queried_repos[count.index].query
}

output "all_repos" {
  value = local.all_repos
}

data "github_user" "current" {
  username = ""
}