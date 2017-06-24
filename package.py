# --------------------------------------------
# 功能：编译xcode项目并打ipa包
# 使用说明：
# 		编译project
# 			ipa-build <project directory> [-c <project configuration>] [-o <ipa output directory>] [-t <target name>] [-n] [-p <platform identifier>]
# 		编译workspace
# 			ipa-build  <workspace directory> -w -s <schemeName> [-c <project configuration>] [-n]
#
# 参数说明： -c NAME				工程的configuration,默认为Release。
# 			-o PATH				生成的ipa文件输出的文件夹（必须为已存在的文件路径）默认为工程根路径下的”build/ipa-build“文件夹中
# 			-t NAME				需要编译的target的名称
# 			-w					编译workspace
# 			-s NAME				对应workspace下需要编译的scheme
# 			-n					编译前是否先clean工程
# 			-p					平台标识符
#           -u                  是否需要上传SVN
#           -v                  SVN文件夹路径
#           -m                  SVN中packageName
import getopt,sys,os,shutil,plistlib,datetime,time

project_path = ''
output_path = ''
build_config='Release'
target_name = ''
should_clean = ''
build_workspace =''
build_scheme = ''
platform_id = ''
appdirname = ''
compiled_path = ''
upload_svn = False
svn_path = ''
svn_packageConfigName = ''
build_path = ''
temp_build_path = ''
temp_output_path = ''
ipa_name = ''
bundleShortVersion = ''
bundleVersion = ''
displayName = ''

def checkDirectoryExist(path):
        if(os.path.exists(path)):
            return True
        else:
            os.makedirs(path)
            return False


def getOptions(opt):
    global build_config,project_path,output_path,target_name,build_workspace,build_scheme,should_clean,platform_id,svn_path,upload_svn,svn_packageConfigName
    for op, value in opt:
        if op == "-c":
            build_config = value
        elif op == "-f":
            project_path = value
        elif op == "-o":
            output_path = value
        elif op == "-t":
            target_name = value
        elif op == "-w":
            build_workspace = value
        elif op == "-s":
            build_scheme = value
        elif op == "-n":
            should_clean = True
        elif op == "-p":
            platform_id = value
        elif op == "-v":
            svn_path = value
        elif op == "-u":
            upload_svn = True
        elif op == "-m":
            svn_packageConfigName = value
        else:
            sys.exit()


def loadParams():
    global compiled_path,temp_build_path,appdirname,build_path,build_config,project_path,output_path,target_name,build_workspace,build_scheme,should_clean,platform_id,svn_path,upload_svn,svn_packageConfigName
    os.chdir(project_path)
    if (upload_svn):
        print(svn_path)
        if (os.path.exists(svn_path) == False):
            print("SVN Path Illegal")
            upload_svn = False


    build_path = project_path + '/build'
    temp_build_path = project_path
    temp_output_path = project_path + '/ipa-build'

    print('++++++++++' + build_path)

    checkDirectoryExist(temp_build_path)

    if(len(output_path) == 0 ):
        output_path = temp_output_path
        checkDirectoryExist(output_path)


    #生成的app文件目录
    appdirname = 'Release-iphoneos'
    if(build_config == 'Debug'):
        appdirname = "Debug-iphoneos"
    elif(build_config == 'Distribute'):
        appdirname = "Distribute-iphoneos"

    #编译后文件路径(仅当编译workspace时才会用到)
    if(len(build_workspace) > 0 ):
        compiled_path = build_path + '/' + appdirname


def clean():
    #是否clean
    if (should_clean):
        os.system('xcodebuild clean -configuration %s'%build_config)
        print("********************* Clean end *******************")
def build():
    global target_name,build_workspace,build_scheme,build_config,build_path
    build_cmd='xcodebuild'

    if(len(build_workspace) > 0):
        if(build_scheme ==''):
            print('Error! Must provide a scheme by -s option together when using -w option to compile a workspace.')
        exit(0)
        os.system(build_cmd + '-list')
        build_cmd = build_cmd + ' -workspace ' + build_workspace + ' -scheme ' + build_scheme + ' -configuration ' + build_config + ' CONFIGURATION_BUILD_DIR=' + compiled_path + ' ONLY_ACTIVE_ARCH=NO '
        print("********************* Schemes end *******************")
    else:
        build_cmd = build_cmd + ' -configuration ' + build_config
        if(len(target_name) > 0):
            build_cmd = build_cmd + ' -target ' + target_name

    #编译工程
    print('---------------project_path ' + project_path)
    os.system(build_cmd)
    print("********************* Build end *******************")

def prepareForPackage():
    global build_path,target_name,ipa_name,bundleVersion,bundleShortVersion,displayName
    # 进入build路径
    os.chdir(build_path)
    # 创建ipa-build文件夹
    checkDirectoryExist(build_path + '/ipa-build')

    # app文件名称
    appname = os.path.basename('%s.app' % target_name)

    # 通过app文件名获得工程target名字
    target_name = appname.split('.')[0]
    # app文件中Info.plist文件路径
    app_infoplist = build_path + '/' + appdirname + '/' + appname + '/Info.plist'

    plist_root = plistlib.readPlist(app_infoplist)

    # 取版本号
    bundleShortVersion = plist_root['CFBundleShortVersionString']
    # 取build值
    bundleVersion = plist_root['CFBundleVersion']
    # 取displayName
    displayName = plist_root['CFBundleDisplayName']

    # IPA名称
    ipa_name = target_name
# xcrun打包
def package():
    os.system('xcrun -sdk iphoneos PackageApplication -v ./%s/*.app -o %s/ipa-build/%s.ipa' % (
    appdirname, build_path, ipa_name))

    print("********************* Package end *******************")

# 导出ipa包
def importPackage():
    global build_path,ipa_name,output_path,svn_packageConfigName,packageName,temp_build_path,temp_output_path
    oldFilePath = build_path + '/ipa-build/' + ipa_name + '.ipa'
    newFilePath = output_path + '/' + ipa_name + '.ipa'
    if (len(output_path) > 0 and os.path.exists(oldFilePath)):
        shutil.copyfile(oldFilePath, newFilePath)
        print("********************* Copy end *******************")
        print('Copy ipa file successfully to the path %s', newFilePath)
        if (upload_svn):
            svnFilePath = ''
            packageName = ipa_name + str(bundleShortVersion) + (
            ('_' + svn_packageConfigName) if (len(svn_packageConfigName) > 0)  else '') + '.ipa'
            svnFilePath = svn_path + '/' + packageName
            shutil.copyfile(oldFilePath, svnFilePath)
        os.chdir(temp_build_path)
        os.system('rm -rf build/')
    else:
        print('package not found')

def commitSvn():
    print('commit svn')


opts, args = getopt.getopt(sys.argv[1:], "f:p:nc:o:t:w:s:uv:m:")
getOptions(opts)
loadParams()
def runToPackage():
    clean()
    build()
    prepareForPackage()
    package()
    importPackage()
    commitSvn()

starttime = datetime.datetime.now()
runToPackage()
print(datetime.datetime.now() - starttime)