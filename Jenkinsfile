// Jenkinsfile (Declarative Pipeline Syntax)
pipeline {
    agent any // 可以在这里指定更具体的 agent，例如 'agent { docker { image 'maven:3.8-jdk-17' } }' }
    
    environment {
        // 环境变量，便于后续修改
        GIT_REPO    = 'https://github.com/wen0668/mcp-jenkins-scenario.git'
        GIT_BRANCH  = 'feature-20260615'
        SSH_OPTS    = '-o StrictHostKeyChecking=no -o ConnectTimeout=10'        
        MAVEN_OPTS = "-Dmaven.repo.local=.m2/repository"
        IMAGE_NAME = "mcp-test-service"
        IMAGE_TAG = "${env.BUILD_ID ?: 'latest'}"
    }
    
    stages {
        stage('Checkout Source Code') {
            steps {
                script {
                    echo '正在拉取源代码...'
                    // **如果您知道需要拉取的仓库和分支，并且希望它覆盖默认行为，请使用如下模式：**
                    checkout([$class: 'GitSCM',
                      branches: [[name: "${GIT_BRANCH}"]],
                      userRemoteConfigs: [[url: "${GIT_REPO}"]]
                ])
            }
          }
        }
        
        stage('Build & Unit Test') {
            steps {
                script {
                    echo '执行 Maven 清理和编译，并运行单元测试...'
                    // 假设使用 Maven 进行构建
                    echo 'sh -x mvn clean package -DskipTests'
                    
                    // 可以在这里添加更详细的测试步骤，例如：
                    // sh "./mvnw test" 
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    // 假设您的Dockerfile位于项目根目录
                    echo "构建 Docker 镜像..."
                    echo 'sh docker build -t myregistry/myapp:${BUILD_ID} .'
                    echo "Docker 镜像构建完成。"
                }
            }
        }
        
        stage('Publish Image') {
            steps {
                script {
                    echo "推送 Docker 镜像到私有仓库..."
                    // 假设您已登录到Docker Registry
                    echo 'sh docker push myregistry/myapp:${BUILD_ID}'
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'master' // 只有推送到 master 分支时才执行部署
            }
            steps {
                script {
                    echo "部署到 Staging 环境..."
                    // 示例：执行部署脚本，该脚本应包含部署到目标环境的逻辑
                    sh "./deploy-script.sh --environment=staging --image=myregistry/myapp:${BUILD_ID}"
                }
            }
        }
    }
}