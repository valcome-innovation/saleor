node {
    withCredentials([sshUserPrivateKey(credentialsId: 'ARES_SSH', keyFileVariable: 'identity', passphraseVariable: 'passphrase', usernameVariable: 'user')]) {
        stage("Build Image") {
            try {
                trigger_build(user, passphrase, identity)
            } catch (e) {
                currentBuild.result = 'FAILURE'
                echo e
            } finally {
                notify_slack()
            }
        }
    }
}

def trigger_build(user, passphrase, identity) {
    def build = start_build(user, passphrase, identity)
    def runningBuild = get_build_status(user, passphrase, identity, build.id)

    while(runningBuild.currentPhase != "COMPLETED") {
        sleep 15
        runningBuild = get_build_status(user, passphrase, identity, build.id)
        echo "ID: " + runningBuild.id
        echo "Phase: " + runningBuild.currentPhase
        echo "Status: " + runningBuild.buildStatus
    }

    sleep 3

    if (runningBuild.buildStatus == "STOPPED") {
      currentBuild.result = 'ABORTED'
    } else if (runningBuild.buildStatus != "SUCCEEDED") {
      currentBuild.result = 'FAILURE'
    }
}

def start_build(user, passphrase, identity) {
    def result = sshCommand remote: get_remote(user, passphrase, identity), command: """
    aws codebuild start-build \
        --project-name saleor \
        --source-version refs/heads/${BRANCH} \
        --environment-variables-override \
            name=TAG,value=${VERSION} \
            name=STATIC_URL,value=${STATIC_URL}
    """
    def json = readJSON text: "" + result
    return json.build
}

def get_build_status(user, passphrase, identity, build_id) {
    def result = sshCommand remote: get_remote(user, passphrase, identity), command: """
    aws codebuild batch-get-builds --ids ${build_id}
    """
    def json = readJSON text: "" + result
    return json.builds[0]
}

def get_remote(user, passphrase, identity) {
    def remote = [:]
    remote.name = "Build Server"
    remote.host = "${HOST}"
    remote.user = user
    remote.passphrase = passphrase
    remote.identityFile = identity
    remote.allowAnyHosts = true
    return remote
}

def notify_slack() {
    def COLOR_MAP = ['SUCCESS': 'good', 'FAILURE': 'danger', 'UNSTABLE': 'warning', 'ABORTED': 'danger']
    def color = COLOR_MAP[currentBuild.currentResult]

    slackSend channel: '#jenkins', color: color, message: get_message()
}

def get_message() {
    return """
*${env.JOB_BASE_NAME} #${env.BUILD_NUMBER}*
${currentBuild.currentResult} ${get_emoji()}

*Image*
saleor

*Version*
${VERSION}

*Branch*
${BRANCH}

_finished in ${currentBuild.durationString}_
"""
}

def get_emoji() {
    def EMOJI_MAP = ['SUCCESS': ':etherwood:', 'FAILURE': ':rotating_light:', 'UNSTABLE': ':oblivion:', 'ABORTED': ':gollum:']
    return EMOJI_MAP[currentBuild.currentResult]
}
