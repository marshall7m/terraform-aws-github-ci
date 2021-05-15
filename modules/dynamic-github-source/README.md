# dynamic-github-source

## Problem ##

Current implementation of AWS CodeBuild doesn't allow for dynamic repo and branch source. CodeBuild does allow for up to 12 secondary sources, although the buildspec would have to have additional logic to explicitly switch to the secondary source that was trigger via the CodeBuild Webhook. Another painful workaround is to create a Codebuild project for each repository. If each repo requires the same CodeBuild configurations, this can lead to multiple copies of the same CodeBuild project but with different sources. This can consequently clutter your AWS CodeBuild workspace especially if there are hundreds of repositories are included in this process.

## Process ##

#TODO: Add CloudCraft flow diagram here

### Steps ###

1. Github event is performed (e.g. user pushes new file, opens PR, etc.) that falls under one of the repository's event filters
2. Github webhook sends a POST HTTP method request to the API Gateway's (AGW) REST API 
3. AGW request integration maps the request to a format friendly format `{'headers': <Webhook headers>, 'body': <Webhook payload>}
4. Processed request is passed to the request validator function that compares the `sha256` value from the request header with the `sha256` value created with the Github secret value and request payload. If the values are equal, the Lambda function succeeds.
5. The payload validator Lambda function is invoked asynchronously on success of the request validor Lambda Function. Payload validator function compares the payload to the filter groups. If the payload passes one of the filter groups, the Codebuild project is kicked off with the triggered repository's CodeBuild configurations ONLY for this build (after this build, CodeBuild project reverts to original configurations).
6. CodeBuild performs the defined buildspec logic


## Usage

Minimal viable configuration:

```
module "dynamic_github_source" {
  source                         = "github.com/marshall7m/terraform-aws-codebuild/modules//dynamic-github-source"
  create_github_secret_ssm_param = true
  github_secret_ssm_value        = var.github_secret_ssm_value
  github_token_ssm_value         = var.github_token
  codebuild_buildspec            = file("buildspec.yaml")
  repos = [
    {
      name = "test-repo"
      filter_groups = [
        {
          events     = ["push"]
        }
      ]
    }
  ]
}
```

Configure repo specific codebuild configurations via `codebuild_cfg` within `repos` list:

```
module "dynamic_github_source" {
  source                         = "github.com/marshall7m/terraform-aws-codebuild/modules//dynamic-github-source"
  create_github_secret_ssm_param = true
  github_secret_ssm_value        = var.github_secret_ssm_value
  github_token_ssm_value         = var.github_token
  codebuild_name                 = "test-codebuild"
  codebuild_buildspec            = file("buildspec.yaml")
  repos = [
    {
      name = "test-repo"
      codebuild_cfg = {
        environment_variables = [
          {
            name  = "TEST"
            value = "FOO"
            type  = "PLAINTEXT"
          }
        ]
      }
      filter_groups = [
        {
          events     = ["push"]
          file_paths = ["CHANGELOG.md"]
        },
        {
          events     = ["pull_request"]
          pr_actions = ["opened", "edited", "synchronize"]
          file_paths = [".*\\.py$"]
          head_refs  = ["test-branch"]
        }
      ]
    }
  ]
}
```

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| terraform | 0.15.0 |
| aws | >= 2.23 |
| github | >= 4.4.0 |

## Providers

| Name | Version |
|------|---------|
| archive | n/a |
| aws | >= 2.23 |
| local | n/a |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| api\_description | Description for API-Gateway | `string` | `null` | no |
| api\_name | Name of API-Gateway | `string` | `"custom-github-webhook"` | no |
| codebuild\_artifacts | Build project's primary output artifacts configuration<br>see for more info: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codebuild_project#argument-reference | <pre>object({<br>    type                   = optional(string)<br>    artifact_identifier    = optional(string)<br>    encryption_disabled    = optional(bool)<br>    override_artifact_name = optional(bool)<br>    location               = optional(string)<br>    name                   = optional(string)<br>    namespace_type         = optional(string)<br>    packaging              = optional(string)<br>    path                   = optional(string)<br>  })</pre> | `{}` | no |
| codebuild\_assumable\_role\_arns | List of IAM role ARNS the Codebuild project can assume | `list(string)` | `[]` | no |
| codebuild\_buildspec | Content of the default buildspec file | `string` | `null` | no |
| codebuild\_cache | Cache configuration for Codebuild project | <pre>object({<br>    type     = optional(string)<br>    location = optional(string)<br>    modes    = optional(list(string))<br>  })</pre> | `{}` | no |
| codebuild\_cw\_group\_name | CloudWatch group name | `string` | `null` | no |
| codebuild\_cw\_logs | Determines if CloudWatch logs should be enabled | `bool` | `true` | no |
| codebuild\_cw\_stream\_name | CloudWatch stream name | `string` | `null` | no |
| codebuild\_description | CodeBuild project description | `string` | `null` | no |
| codebuild\_environment | Codebuild environment configuration | <pre>object({<br>    compute_type                = optional(string)<br>    image                       = optional(string)<br>    type                        = optional(string)<br>    image_pull_credentials_type = optional(string)<br>    environment_variables = optional(list(object({<br>      name  = string<br>      value = string<br>      type  = optional(string)<br>    })))<br>    privileged_mode = optional(bool)<br>    certificate     = optional(string)<br>    registry_credential = optional(object({<br>      credential          = optional(string)<br>      credential_provider = optional(string)<br>    }))<br>  })</pre> | `{}` | no |
| codebuild\_name | Name of Codebuild project | `string` | n/a | yes |
| codebuild\_role\_arn | Existing IAM role ARN to attach to CodeBuild project | `string` | `null` | no |
| codebuild\_s3\_log\_bucket | Name of S3 bucket where the build project's logs will be stored | `string` | `null` | no |
| codebuild\_s3\_log\_encryption | Determines if encryption should be disabled for the build project's S3 logs | `bool` | `false` | no |
| codebuild\_s3\_log\_key | Bucket path where the build project's logs will be stored (don't include bucket name) | `string` | `null` | no |
| codebuild\_secondary\_artifacts | Build project's secondary output artifacts configuration | <pre>object({<br>    type                   = optional(string)<br>    artifact_identifier    = optional(string)<br>    encryption_disabled    = optional(bool)<br>    override_artifact_name = optional(bool)<br>    location               = optional(string)<br>    name                   = optional(string)<br>    namespace_type         = optional(string)<br>    packaging              = optional(string)<br>    path                   = optional(string)<br>  })</pre> | `{}` | no |
| codebuild\_tags | Tags to attach to Codebuild project | `map(string)` | `{}` | no |
| codebuild\_timeout | Minutes till build run is timed out | `string` | `null` | no |
| common\_tags | Tags to add to all resources | `map(string)` | `{}` | no |
| create\_github\_secret\_ssm\_param | Determines if a SSM parameter should be created for github webhook secret | `bool` | `false` | no |
| enable\_codebuild\_s3\_logs | Determines if S3 logs should be enabled | `bool` | `false` | no |
| function\_name | Name of AWS Lambda function | `string` | `"custom-codebuild-github-webhook-trigger"` | no |
| github\_secret\_ssm\_description | Github secret SSM parameter description | `string` | `"Secret value for Github Webhooks"` | no |
| github\_secret\_ssm\_key | SSM parameter store key for github webhook secret. Secret used within Lambda function for Github request validation. | `string` | `"github-webhook-secret"` | no |
| github\_secret\_ssm\_tags | Tags for Github webhook secret SSM parameter | `map(string)` | `{}` | no |
| github\_secret\_ssm\_value | SSM parameter store value for github webhook secret. Secret used within Lambda function for Github request validation. | `string` | `""` | no |
| github\_token\_ssm\_description | Github token SSM parameter description | `string` | `"Github token used to give read access to the payload validator function to get file that differ between commits"` | no |
| github\_token\_ssm\_key | AWS SSM Parameter Store key for sensitive Github personal token | `string` | `"read-acces-github-token"` | no |
| github\_token\_ssm\_tags | Tags for Github token SSM parameter | `map(string)` | `{}` | no |
| github\_token\_ssm\_value | Registered Github webhook token associated with the Github provider. If not provided, module looks for pre-existing SSM parameter via `github_token_ssm_key` | `string` | `""` | no |
| repos | List of named repos to create github webhooks for and their respective filter groups used to select<br>what type of activity will trigger the associated Codebuild.<br>Params:<br>  `name`: Repository name<br>  `codebuild_cfg`: CodeBuild configurations specifically for the repository<br>  `filter_groups`: {<br>    `events` - List of Github Webhook events that will invoke the API. Currently only supports: `push` and `pull_request`.<br>    `pr_actions` - List of pull request actions (e.g. opened, edited, reopened, closed). See more under the action key at: https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#pull_request<br>    `base_refs` - List of base refs<br>    `head_refs` - List of head refs<br>    `actor_account_ids` - List of Github user IDs<br>    `commit_messages` - List of commit messages<br>    `file_paths` - List of file paths<br>    `exclude_matched_filter` - If set to true, Codebuild project will not be triggered by this filter if it is matched<br>  } | <pre>list(object({<br>    name = string<br><br>    codebuild_cfg = optional(object({<br>      buildspec = optional(string)<br>      timeout   = optional(string)<br>      cache = optional(object({<br>        type     = optional(string)<br>        location = optional(string)<br>        modes    = optional(list(string))<br>      }))<br>      report_build_status = optional(bool)<br>      environment_type    = optional(string)<br>      compute_type        = optional(string)<br>      image               = optional(string)<br>      environment_variables = optional(list(object({<br>        name  = string<br>        value = string<br>        type  = optional(string)<br>      })))<br>      privileged_mode = optional(bool)<br>      certificate     = optional(string)<br>      artifacts = optional(object({<br>        type                   = optional(string)<br>        artifact_identifier    = optional(string)<br>        encryption_disabled    = optional(bool)<br>        override_artifact_name = optional(bool)<br>        location               = optional(string)<br>        name                   = optional(string)<br>        namespace_type         = optional(string)<br>        packaging              = optional(string)<br>        path                   = optional(string)<br>      }))<br>      secondary_artifacts = optional(object({<br>        type                   = optional(string)<br>        artifact_identifier    = optional(string)<br>        encryption_disabled    = optional(bool)<br>        override_artifact_name = optional(bool)<br>        location               = optional(string)<br>        name                   = optional(string)<br>        namespace_type         = optional(string)<br>        packaging              = optional(string)<br>        path                   = optional(string)<br>      }))<br>      role_arn = optional(string)<br>      logs_cfg = optional(object({<br>        cloudWatchLogs = optional(object({<br>          status     = string<br>          groupName  = string<br>          streamName = string<br>        }))<br>        s3Logs = optional(object({<br>          status   = string<br>          location = string<br>        }))<br>      }))<br>    }))<br><br>    filter_groups = list(object({<br>      events                 = list(string)<br>      pr_actions             = optional(list(string))<br>      base_refs              = optional(list(string))<br>      head_refs              = optional(list(string))<br>      actor_account_ids      = optional(list(string))<br>      commit_messages        = optional(list(string))<br>      file_paths             = optional(list(string))<br>      exclude_matched_filter = optional(bool)<br>    }))<br>  }))</pre> | `[]` | no |

## Outputs

| Name | Description |
|------|-------------|
| api\_invoke\_url | n/a |
| codebuild\_arn | n/a |
| github\_token\_ssm\_key | n/a |
| payload\_filter\_function\_arn | n/a |
| repo\_cfg | n/a |
| request\_validator\_function\_arn | n/a |

<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
