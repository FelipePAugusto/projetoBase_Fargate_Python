/* Common */
variable "aws_region" {
  type        = string
  description = "This is the AWS region."
  default     = "us-east-2"
}

variable "environment_name" {
  type        = string
  description = "Application environment name."
}

variable "app_name" {
  type        = string
  description = "Application name."
}

variable "commercial_name" {
  type        = string
  description = "Application commercial name."
  default     = ""
}

variable "github_token" {
  type        = string
  description = "Github Token for cloning the project repository. Flags=SENSITIVE"
}

/* ECS */
variable "container_names" {
  type        = list(string)
  description = "Name of each container. Only use this option when deploying multi-tier container environment. Flags=HCL"
}

variable "container_ports" {
  type        = list(number)
  description = "The port value, already specified in the task definition, to be used for your service discovery service. Flags=HCL"
}

variable "container_memory" {
  type        = number
  description = "The amount (in MiB) of memory used by the task."
  default     = 1024
}

variable "container_cpu" {
  type        = number
  description = "The number of cpu units used by the task."
  default     = 512
}

variable "task_desired_count" {
  type        = number
  description = "The number of instances of the task definition to place and keep running."
  default     = 1
}

/* Loadbalancer */
variable "autoscaling_capacity" {
  type        = map(number)
  description = "The min capacity of the scalable target. Flags=HCL"
  default = {
    min = 1
    max = 4
  }
}

variable "health_check_path" {
  type        = string
  description = "The destination for the health check request."
  default     = "/alive"
}
