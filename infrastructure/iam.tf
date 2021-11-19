/* CodeBuild */
resource "aws_iam_role" "codebuild_role" {
  name               = "CodeBuildRole-${var.app_name}"
  assume_role_policy = file("${path.module}/iam/CodeBuildTrustPolicy.json")
  tags               = local.common_tags

  force_detach_policies = true

  lifecycle {
    create_before_destroy = false
  }
}

data "template_file" "codebuild_policy" {
  template = file("${path.module}/iam/CodeBuildPolicy.json")

  vars = {
    aws_s3_bucket_arn = data.aws_s3_bucket.source.arn
    aws_region        = var.aws_region
    account_id        = data.aws_caller_identity.current.account_id
    app_name          = var.app_name
  }
}

resource "aws_iam_role_policy" "codebuild_policy" {
  name   = "CodeBuildPolicy-${var.app_name}"
  role   = aws_iam_role.codebuild_role.id
  policy = data.template_file.codebuild_policy.rendered

  lifecycle {
    create_before_destroy = false
  }
}

/* CodePipeline */
resource "aws_iam_role" "codepipeline_role" {
  name               = "CodePipelineRole-${var.app_name}"
  assume_role_policy = file("${path.module}/iam/CodePipelineTrustPolicy.json")
  tags               = local.common_tags

  force_detach_policies = true

  lifecycle {
    create_before_destroy = false
  }
}

data "template_file" "codepipeline_policy" {
  template = file("${path.module}/iam/CodePipelinePolicy.json")
  vars = {
    aws_s3_bucket_arn = data.aws_s3_bucket.source.arn
  }
}

resource "aws_iam_role_policy" "codepipeline_policy" {
  name   = "CodePipelinePolicy-${var.app_name}"
  role   = aws_iam_role.codepipeline_role.id
  policy = data.template_file.codepipeline_policy.rendered

  lifecycle {
    create_before_destroy = false
  }
}

/* Secrets Manager */
data "template_file" "secrets_permissions" {
  template = file("${path.module}/iam/SecretsManagerPolicy.json")
  vars = {
    app_name   = var.app_name
    aws_region = var.aws_region
    account_id = data.aws_caller_identity.current.account_id
  }
}

resource "aws_iam_policy" "secrets_policy" {
  name   = "ECSSecretsManagerPolicy-${var.app_name}"
  policy = data.template_file.secrets_permissions.rendered

  lifecycle {
    create_before_destroy = false
  }
}

resource "aws_iam_role_policy_attachment" "attach_secrets_permission_to_role" {
  policy_arn = aws_iam_policy.secrets_policy.arn
  role       = module.ecs.ecs_task_role["name"]
}
