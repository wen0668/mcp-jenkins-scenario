// Jenkinsfile (Declarative Pipeline) for mcp-jenkins-scenario
// Python-based Jenkins MCP Server

pipeline {
    agent any

    environment {
        GIT_REPO          = 'https://github.com/wen0668/mcp-jenkins-scenario.git'
        JENKINS_URL       = 'http://192.168.0.4:8080'
        JENKINS_USERNAME  = 'mcp-dev'
        JENKINS_API_TOKEN = '114144a252560bf1709ca15bf4a53ace19'
        IMAGE_NAME         = 'mcp-jenkins-scenario'
    }

    parameters {
        string(name: 'GIT_BRANCH', defaultValue: 'feature-20260615', description: 'Git 分支')
        string(name: 'DEPLOY_ENV', defaultValue: 'staging', description: '部署环境 (staging/production)')
        booleanParam(name: 'RUN_TESTS', defaultValue: true, description: '是否运行测试')
    }

    stages {
        stage('Checkout Source Code') {
            steps {
                script {
                    echo "正在拉取源代码: ${GIT_REPO}, 分支: ${params.GIT_BRANCH}"
                    checkout([$class: 'GitSCM',
                        branches: [[name: "*/${params.GIT_BRANCH}"]],
                        userRemoteConfigs: [[url: "${GIT_REPO}"]]
                    ])
                }
            }
        }

        stage('Setup Python Environment') {
            steps {
                script {
                    echo '配置 Python 虚拟环境...'
                }
            }
        }

        stage('Unit Test') {
            when {
                expression { params.RUN_TESTS }
            }
            steps {
                script {
                    echo '运行单元测试...'
                }
            }
        }

        stage('Verify') {
            steps {
                script {
                  echo '正在验证构建结构...'                  
                }
            }
        }

        stage('Deploy') {
            when {
                expression { params.DEPLOY_ENV == 'production' || params.DEPLOY_ENV == 'staging' }
            }
            steps {
                script {
                    echo "部署到 ${params.DEPLOY_ENV} 环境..."
                    sh '''
                        echo "MCP Server 部署完成"
                    '''
                }
            }
        }
    }

    post {
        always {
            echo "流水线执行完毕。"
            cleanWs()
        }
        success {
            echo "构建成功！"
        }
        failure {
            echo "构建失败，请检查日志。"
        }
    }
}
