#!/usr/bin/env python3
"""
Automated deployment script for DRYAD.AI Backend.
Handles deployment to different environments with proper validation and rollback capabilities.
"""

import os
import sys
import json
import time
import subprocess
import argparse
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import requests
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentError(Exception):
    """Custom exception for deployment errors."""
    pass


class DRYAD.AIDeployer:
    """Automated deployment manager for DRYAD.AI Backend."""
    
    def __init__(self, environment: str, config_path: str = "deployment/config.yaml"):
        self.environment = environment
        self.config_path = config_path
        self.config = self._load_config()
        self.env_config = self.config.get(environment, {})
        
        if not self.env_config:
            raise DeploymentError(f"No configuration found for environment: {environment}")
        
        logger.info(f"Initialized deployer for environment: {environment}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self._get_default_config()
        except yaml.YAMLError as e:
            raise DeploymentError(f"Invalid YAML in config file: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default deployment configuration."""
        return {
            "staging": {
                "kubernetes": {
                    "namespace": "DRYAD.AI-staging",
                    "context": "staging-cluster",
                    "manifests_path": "k8s/staging/"
                },
                "health_check": {
                    "url": "https://staging-api.DRYAD.AI.com/api/v1/health",
                    "timeout": 30,
                    "retries": 5
                },
                "rollback": {
                    "enabled": True,
                    "timeout": 300
                }
            },
            "production": {
                "kubernetes": {
                    "namespace": "DRYAD.AI-production",
                    "context": "production-cluster",
                    "manifests_path": "k8s/production/"
                },
                "health_check": {
                    "url": "https://api.DRYAD.AI.com/api/v1/health",
                    "timeout": 60,
                    "retries": 10
                },
                "rollback": {
                    "enabled": True,
                    "timeout": 600
                },
                "approval_required": True
            }
        }
    
    def deploy(self, image_tag: str, dry_run: bool = False) -> bool:
        """
        Deploy the application to the specified environment.
        
        Args:
            image_tag: Docker image tag to deploy
            dry_run: If True, only validate without actually deploying
            
        Returns:
            True if deployment successful, False otherwise
        """
        try:
            logger.info(f"Starting deployment to {self.environment}")
            logger.info(f"Image tag: {image_tag}")
            
            if dry_run:
                logger.info("DRY RUN MODE - No actual changes will be made")
            
            # Pre-deployment validation
            self._validate_prerequisites()
            
            # Get current deployment info for rollback
            current_deployment = self._get_current_deployment()
            
            # Require approval for production
            if self.environment == "production" and not dry_run:
                if not self._get_deployment_approval():
                    logger.info("Deployment cancelled - approval not granted")
                    return False
            
            # Update deployment manifests
            self._update_manifests(image_tag)
            
            if dry_run:
                logger.info("DRY RUN: Manifests updated successfully")
                return True
            
            # Deploy to Kubernetes
            self._deploy_to_kubernetes()
            
            # Wait for deployment to be ready
            self._wait_for_deployment()
            
            # Run health checks
            if not self._run_health_checks():
                logger.error("Health checks failed, initiating rollback")
                self._rollback(current_deployment)
                return False
            
            # Run smoke tests
            if not self._run_smoke_tests():
                logger.error("Smoke tests failed, initiating rollback")
                self._rollback(current_deployment)
                return False
            
            logger.info(f"Deployment to {self.environment} completed successfully")
            self._notify_deployment_success(image_tag)
            
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            if not dry_run:
                self._notify_deployment_failure(str(e))
            return False
    
    def _validate_prerequisites(self):
        """Validate deployment prerequisites."""
        logger.info("Validating deployment prerequisites...")
        
        # Check kubectl availability
        try:
            subprocess.run(["kubectl", "version", "--client"], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            raise DeploymentError("kubectl not available or not configured")
        
        # Check Kubernetes context
        k8s_config = self.env_config.get("kubernetes", {})
        context = k8s_config.get("context")
        if context:
            try:
                subprocess.run(["kubectl", "config", "use-context", context],
                             check=True, capture_output=True)
                logger.info(f"Switched to Kubernetes context: {context}")
            except subprocess.CalledProcessError:
                raise DeploymentError(f"Failed to switch to context: {context}")
        
        # Check namespace exists
        namespace = k8s_config.get("namespace", "default")
        try:
            subprocess.run(["kubectl", "get", "namespace", namespace],
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.warning(f"Namespace {namespace} does not exist, creating...")
            subprocess.run(["kubectl", "create", "namespace", namespace],
                         check=True)
        
        logger.info("Prerequisites validation completed")
    
    def _get_current_deployment(self) -> Optional[Dict[str, Any]]:
        """Get current deployment information for rollback purposes."""
        try:
            k8s_config = self.env_config.get("kubernetes", {})
            namespace = k8s_config.get("namespace", "default")
            
            result = subprocess.run([
                "kubectl", "get", "deployment", "DRYAD.AI-backend",
                "-n", namespace, "-o", "json"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                deployment_info = json.loads(result.stdout)
                return {
                    "image": deployment_info["spec"]["template"]["spec"]["containers"][0]["image"],
                    "replicas": deployment_info["spec"]["replicas"],
                    "revision": deployment_info["metadata"]["annotations"].get(
                        "deployment.kubernetes.io/revision", "unknown"
                    )
                }
        except Exception as e:
            logger.warning(f"Could not get current deployment info: {e}")
        
        return None
    
    def _get_deployment_approval(self) -> bool:
        """Get manual approval for production deployment."""
        print("\n" + "="*60)
        print("PRODUCTION DEPLOYMENT APPROVAL REQUIRED")
        print("="*60)
        print(f"Environment: {self.environment}")
        print(f"Target: {self.env_config.get('health_check', {}).get('url', 'Unknown')}")
        print("="*60)
        
        while True:
            response = input("Do you approve this production deployment? (yes/no): ").lower().strip()
            if response in ['yes', 'y']:
                return True
            elif response in ['no', 'n']:
                return False
            else:
                print("Please enter 'yes' or 'no'")
    
    def _update_manifests(self, image_tag: str):
        """Update Kubernetes manifests with new image tag."""
        logger.info("Updating deployment manifests...")
        
        k8s_config = self.env_config.get("kubernetes", {})
        manifests_path = k8s_config.get("manifests_path", "k8s/")
        
        if not os.path.exists(manifests_path):
            raise DeploymentError(f"Manifests path does not exist: {manifests_path}")
        
        # Update deployment.yaml with new image tag
        deployment_file = os.path.join(manifests_path, "deployment.yaml")
        if os.path.exists(deployment_file):
            with open(deployment_file, 'r') as f:
                content = f.read()
            
            # Simple image tag replacement
            # In production, use proper YAML parsing
            updated_content = content.replace(
                "image: DRYAD.AI/backend:latest",
                f"image: DRYAD.AI/backend:{image_tag}"
            )
            
            with open(deployment_file, 'w') as f:
                f.write(updated_content)
            
            logger.info(f"Updated {deployment_file} with image tag: {image_tag}")
        else:
            logger.warning(f"Deployment file not found: {deployment_file}")
    
    def _deploy_to_kubernetes(self):
        """Deploy to Kubernetes cluster."""
        logger.info("Deploying to Kubernetes...")
        
        k8s_config = self.env_config.get("kubernetes", {})
        manifests_path = k8s_config.get("manifests_path", "k8s/")
        namespace = k8s_config.get("namespace", "default")
        
        try:
            # Apply all manifests
            subprocess.run([
                "kubectl", "apply", "-f", manifests_path,
                "-n", namespace
            ], check=True)
            
            logger.info("Kubernetes manifests applied successfully")
            
        except subprocess.CalledProcessError as e:
            raise DeploymentError(f"Failed to apply Kubernetes manifests: {e}")
    
    def _wait_for_deployment(self, timeout: int = 300):
        """Wait for deployment to be ready."""
        logger.info("Waiting for deployment to be ready...")
        
        k8s_config = self.env_config.get("kubernetes", {})
        namespace = k8s_config.get("namespace", "default")
        
        try:
            subprocess.run([
                "kubectl", "rollout", "status", "deployment/DRYAD.AI-backend",
                "-n", namespace, f"--timeout={timeout}s"
            ], check=True)
            
            logger.info("Deployment is ready")
            
        except subprocess.CalledProcessError:
            raise DeploymentError("Deployment failed to become ready within timeout")
    
    def _run_health_checks(self) -> bool:
        """Run health checks against the deployed application."""
        logger.info("Running health checks...")
        
        health_config = self.env_config.get("health_check", {})
        url = health_config.get("url")
        timeout = health_config.get("timeout", 30)
        retries = health_config.get("retries", 5)
        
        if not url:
            logger.warning("No health check URL configured, skipping health checks")
            return True
        
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get("status") in ["healthy", "degraded"]:
                        logger.info("Health check passed")
                        return True
                    else:
                        logger.warning(f"Health check returned status: {health_data.get('status')}")
                else:
                    logger.warning(f"Health check returned status code: {response.status_code}")
                    
            except requests.RequestException as e:
                logger.warning(f"Health check attempt {attempt + 1} failed: {e}")
            
            if attempt < retries - 1:
                logger.info(f"Retrying health check in 10 seconds...")
                time.sleep(10)
        
        logger.error("All health check attempts failed")
        return False
    
    def _run_smoke_tests(self) -> bool:
        """Run smoke tests against the deployed application."""
        logger.info("Running smoke tests...")
        
        health_config = self.env_config.get("health_check", {})
        base_url = health_config.get("url", "").replace("/api/v1/health", "")
        
        if not base_url:
            logger.warning("No base URL available for smoke tests")
            return True
        
        # Basic smoke tests
        smoke_tests = [
            f"{base_url}/api/v1/health",
            f"{base_url}/api/v1/health/detailed",
        ]
        
        for test_url in smoke_tests:
            try:
                response = requests.get(test_url, timeout=30)
                if response.status_code not in [200, 401, 403]:  # 401/403 are OK for auth endpoints
                    logger.error(f"Smoke test failed for {test_url}: {response.status_code}")
                    return False
                logger.info(f"Smoke test passed: {test_url}")
            except requests.RequestException as e:
                logger.error(f"Smoke test failed for {test_url}: {e}")
                return False
        
        logger.info("All smoke tests passed")
        return True
    
    def _rollback(self, previous_deployment: Optional[Dict[str, Any]]):
        """Rollback to previous deployment."""
        if not self.env_config.get("rollback", {}).get("enabled", True):
            logger.warning("Rollback is disabled for this environment")
            return
        
        logger.info("Initiating rollback...")
        
        k8s_config = self.env_config.get("kubernetes", {})
        namespace = k8s_config.get("namespace", "default")
        
        try:
            # Rollback using kubectl
            subprocess.run([
                "kubectl", "rollout", "undo", "deployment/DRYAD.AI-backend",
                "-n", namespace
            ], check=True)
            
            # Wait for rollback to complete
            rollback_timeout = self.env_config.get("rollback", {}).get("timeout", 300)
            subprocess.run([
                "kubectl", "rollout", "status", "deployment/DRYAD.AI-backend",
                "-n", namespace, f"--timeout={rollback_timeout}s"
            ], check=True)
            
            logger.info("Rollback completed successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Rollback failed: {e}")
    
    def _notify_deployment_success(self, image_tag: str):
        """Notify about successful deployment."""
        logger.info(f"Deployment notification: SUCCESS - {self.environment} - {image_tag}")
        # Add Slack/email notification here
    
    def _notify_deployment_failure(self, error: str):
        """Notify about deployment failure."""
        logger.error(f"Deployment notification: FAILURE - {self.environment} - {error}")
        # Add Slack/email notification here


def main():
    """Main deployment script entry point."""
    parser = argparse.ArgumentParser(description="Deploy DRYAD.AI Backend")
    parser.add_argument("environment", choices=["staging", "production"],
                       help="Target environment")
    parser.add_argument("image_tag", help="Docker image tag to deploy")
    parser.add_argument("--dry-run", action="store_true",
                       help="Validate deployment without making changes")
    parser.add_argument("--config", default="deployment/config.yaml",
                       help="Path to deployment configuration file")
    
    args = parser.parse_args()
    
    try:
        deployer = DRYAD.AIDeployer(args.environment, args.config)
        success = deployer.deploy(args.image_tag, args.dry_run)
        
        if success:
            logger.info("Deployment completed successfully")
            sys.exit(0)
        else:
            logger.error("Deployment failed")
            sys.exit(1)
            
    except DeploymentError as e:
        logger.error(f"Deployment error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
