/* Loadbalancer */
resource "aws_lb_target_group" "webserver_target_group" {
  name                 = "${var.app_name}-${var.environment_name}"
  port                 = var.container_ports[0]
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = module.base.vpc_id
  deregistration_delay = "300"

  health_check {
    port     = var.container_ports[0]
    protocol = "HTTP"
    path     = var.health_check_path
  }

  tags = local.common_tags
}

module "loadbalancer" {
  source  = "app.terraform.io/MadeiraMadeira/loadbalancer/aws"
  version = "2.0.1"

  app_name         = var.app_name
  environment_name = var.environment_name
  commercial_name  = var.commercial_name

  create_cname_record    = true
  record_fqdn            = ""
  record_ttl             = 300
  is_internal            = true
  http_port              = 80
  https_port             = 443
  redirect_http_to_https = true
  ssl_policy             = "ELBSecurityPolicy-2016-08"
  target_group_arn       = aws_lb_target_group.webserver_target_group.arn
  hosted_zone_id         = module.base.madeiramadeira_hosted_zone_id

  /* Use shared loadbalancer */
  shared_loadbalancer = {
    "arn"                    = var.environment_name == "production" ? null : module.base.shared_loadbalancer
    "https_listener_arn"     = var.environment_name == "production" ? null : module.base.shared_loadbalancer_listener_443
    "listener_rule_priority" = null # auto-assign priority
  }

  security_group_ids = []
  subnet_ids         = []
  certificate_arn    = ""

  custom_tags = {}
}
