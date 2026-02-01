output "instance_name" {
  description = "Name of the Lightsail instance"
  value       = aws_lightsail_instance.secvault.name
}

output "static_ip" {
  description = "Static IP address - point your domain DNS here"
  value       = aws_lightsail_static_ip.secvault.ip_address
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_lightsail_static_ip.secvault.ip_address}"
}

output "http_url" {
  description = "HTTP URL (before SSL setup)"
  value       = "http://${aws_lightsail_static_ip.secvault.ip_address}"
}

output "https_url" {
  description = "HTTPS URL (after SSL setup with domain)"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "Configure domain_name variable for HTTPS"
}

output "next_steps" {
  description = "Post-deployment steps"
  value       = <<-EOT

    ╔════════════════════════════════════════════════════════════════╗
    ║                     DEPLOYMENT COMPLETE                        ║
    ╠════════════════════════════════════════════════════════════════╣
    ║ Next steps:                                                    ║
    ║                                                                ║
    ║ 1. Wait 2-3 minutes for instance initialization                ║
    ║                                                                ║
    ║ 2. SSH into the instance:                                      ║
    ║    ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_lightsail_static_ip.secvault.ip_address}
    ║                                                                ║
    ║ 3. Configure environment:                                      ║
    ║    cd /opt/secvault                                            ║
    ║    sudo nano .env  # Set production secrets                    ║
    ║                                                                ║
    ║ 4. Start the application:                                      ║
    ║    sudo make prod-build                                        ║
    ║                                                                ║
    ║ 5. (Optional) Setup SSL with your domain:                      ║
    ║    sudo certbot --nginx -d yourdomain.com                      ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
  EOT
}
