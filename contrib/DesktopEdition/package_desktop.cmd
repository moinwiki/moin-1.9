@echo off
rem ToDo:
rem Fix for 1.6
rem Translate to English
rem setup.py, welches die configvariablen abfragt und in sich selbst speichert, browserstartoption
rem bugs fixen (siehe lokales wiki)
rem HowToBuild aktualisieren

set version=Release 1.6.0dev-1
set buildfile=moin-desktop-1.6.0dev-1

rem MoinMoin Quelle
set build=moin--main--1.6
rem set build=z:\root\moin--main--1.3

set sevenzippath=C:\Programme\7-Zip\7z

echo Building DesktopEdition %version% ...

if exist %build% (
	if exist moin-desktop (
		del /Q /F /S moin-desktop >NUL 2>NUL
		rmdir /S /Q moin-desktop
	)
	echo Creating page packages ...
	cd %build%
	make pagepacks
	cd ..
	
	echo Creating base system ...
	md moin-desktop
	xcopy /E /I /Q "%build%\MoinMoin" "moin-desktop\MoinMoin"
	xcopy /E /I /Q "%build%\wiki" "moin-desktop\wiki"
	xcopy /E /I /Q /Y "_underlay\*" "moin-desktop\wiki\underlay\pages\"
	md moin-desktop\docs
	sed -n "/MoinMoin Version History/,/default options for new users are same/p" <"%build%\docs\CHANGES">"moin-desktop\docs\CHANGES"
	xcopy /I /Q "%build%\docs\licenses\COPYING" "moin-desktop\docs"
	xcopy /I /Q "%build%\README" "moin-desktop\docs\"
	copy _resources\moin.py moin-desktop\	>NUL
	copy _resources\wikiconfig.py moin-desktop\	>NUL
	copy "_resources\MoinMoin DesktopEdition.url" moin-desktop\	>NUL
	del /Q /F /S moin-desktop\.cvsignore>NUL
	del /Q /F /S moin-desktop\CVS>NUL
	del /Q /F moin-desktop\MoinMoin\i18n\*.po>NUL
	del moin-desktop\wiki\underlay\pages\SystemPagesSetup\attachments\extra.zip >NUL
	del moin-desktop\MoinMoin\_template.py>NUL
	del moin-desktop\wiki\data\edit-log>NUL
	del moin-desktop\wiki\README.underlay>NUL
	del moin-desktop\wiki\underlay.tar>NUL
	del moin-desktop\wiki\htdocs\index.html>NUL
	del moin-desktop\wiki\htdocs\applets\index.html>NUL
	
	rd /Q /S moin-desktop\wiki\config\>NUL
	rd /Q /S moin-desktop\wiki\server\>NUL
	rd /Q /S moin-desktop\wiki\htdocs\applets\FCKeditor\_samples>NUL 2>NUL
	rd /Q /S moin-desktop\wiki\htdocs\applets\FCKeditor\_testcases>NUL 2>NUL
	del moin-desktop\wiki\htdocs\applets\FCKeditor\_documentation.html>NUL
	del moin-desktop\wiki\htdocs\applets\FCKeditor\_whatsnew.html>NUL
	del moin-desktop\wiki\htdocs\applets\FCKeditor\license.txt>NUL
	
	echo MoinMoin DesktopEdition - packaged by AlexanderSchremmer> moin-desktop\readme_desktop.txt
	echo licensed under GNU GPL, see COPYING>> moin-desktop\readme_desktop.txt
	echo %version%, see the page SystemInfo for exact revision>> moin-desktop\readme_desktop.txt
	echo.>> moin-desktop\readme_desktop.txt
	echo See http://moinmo.in/DesktopEdition for current information.>> moin-desktop\readme_desktop.txt
	echo.>> moin-desktop\readme_desktop.txt
	echo MoinMoin needs Python in order to run. You can download it here: http://www.python.org/download/>> moin-desktop\readme_desktop.txt
	echo Python 2.4.3 is recommended, Python 2.3 is required. Nothing else is needed.>> moin-desktop\readme_desktop.txt
	echo.>> moin-desktop\readme_desktop.txt
	echo In order to start MoinMoin DesktopEdition, just run moin.py>> moin-desktop\readme_desktop.txt
	echo and point your web browser to http://localhost:8080/>> moin-desktop\readme_desktop.txt

	echo.>> moin-desktop\readme_desktop.txt

	del /Q /F /S moin-desktop\*.pyc>NUL 2>NUL

if exist %buildfile%.tbz del %buildfile%.tbz 
if exist %buildfile%.zip del %buildfile%.zip
if exist %buildfile%.exe del %buildfile%.exe
echo Finished base build.
echo.
echo Press CTRL+C if you do not want to have any archives.
echo Otherwise:
pause

echo Creating archives ...

echo ZIP
%sevenzippath% a -r -tzip -mx=9 %buildfile%.zip moin-desktop\*

echo TBZ
tar cjf %buildfile%.tbz moin-desktop

echo Py2EXE
	rem http://starship.python.net/crew/theller/moin.cgi/ExcludingDlls
	cd moin-desktop
	if not exist ..\setup_pyexe.py echo ERROR! setup_pyexe.py not found!
	if exist build\NUL del /Q /F /S build
	if exist dist\NUL del /Q /F /S dist
	python ..\setup_pyexe.py py2exe -x -a
	pause
	del dist\w9xpopen.exe
	rem C:\UTIL\#archiv\upx\upx --best --force dist\_socket.pyd dist\moin.exe
	dir dist

move dist MMDE
move wikiconfig.py MMDE
move docs MMDE\docs
move "MoinMoin DesktopEdition.url" MMDE
move readme_desktop.txt MMDE
move wiki MMDE\wiki

echo 7z,EXE
%sevenzippath% a -r -t7z -sfx7z.sfx -mx=7 ..\%buildfile%.exe MMDE\*
cd ..


echo Created archives.

) ELSE (
	echo %build% was not found!
)
pause

