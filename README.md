Scancopyright is a tool which can be used to scan copyright info of source code,you can use it to identity source code as GPL/other license or propriertary.

I wrote it for the open source of our android source code.

You can:

 * Join the chat at https://gitter.im/zhangchunlin/scancopyright
 * [submit issue](https://github.com/zhangchunlin/scancopyright/issues/new) for improvement or questions.

## Install
Scancopyright can be run cross platform(linux/windows...) in theory,but only linux installration is tested.

### Install dependent modules
Scancopyright depend on python(2.6+)/uliweb/plugs/sqlalchemy,you should install them firstly.
Example steps in ubuntu:

<code>
apt-get install python-setuptools
easy_install uliweb
easy_install plugs
easy_install sqlalchemy
</code>

### Install scancopyright
1. get scancopyright source code

    you can get source code from github:

    <code>
    git clone https://github.com/zhangchunlin/scancopyright.git
    cd scancopyright
    </code>
2. cd source code root directory

## Scan copyright

follow the "uliweb schelp" instructions to use scancopyright(the whole scan process may take a few hours for big source code project i.e. android source code):

```
zhangclb@zhangclb2:~/devel/scancopyright$ uliweb schelp

----- easy way(recommanded) -------
in scancopyright directory:
- ln -s YOUR_TARGET_PROJECT_DIRECTORY target_project (link target project directory)
- make sure in target_project/.repo/project.list having package list you want
- uliweb syncdb (if you want to recreate database use: uliweb reset)
- uliweb scall

----- expert way -----
follow these steps to scan copyright:
- copy apps/local_setting.ini.example as apps/local_setting.ini
- modify local_settings.ini

[SCAN]
DIR = 'YOUR_SOURCE_CODE_PATH'
[ORM]
CONNECTION = 'sqlite:///DATABASE_NAME_YOU_WANT.db'

- uliweb syncdb (if you want to recreate database use: uliweb reset)
- uliweb scap (scan all path)
- uliweb scac (scan all copyright)
- uliweb scdad (decide all direcotry status)
- uliweb scipl (import package list, make sure in target_project/.repo/project.list having package list you want)
- uliweb sceos (export packages)
```

## View scan result and export
1. Run uliweb server

    <code>
    uliweb runserver
    </code>

2. Visit http://localhost:8000 in your browser,google chrome recommanded.

    ![view scan result](/docs/screenshots/screenshot01.png)

3. You can click + icon to expand the directory in tree view

    ![tree view](/docs/screenshots/screenshot02.png)

4. When click a node of tree,you can go to file view

    ![file view](/docs/screenshots/screenshot03.png)

5. Manually import package list (You can also do it using command: uliweb scipl)

    ![import package list](/docs/screenshots/screenshot04.png)

6. Manually export package list (You can also do it using command: uliweb sceos)

    ![export package list](/docs/screenshots/screenshot05.png)

## Config scan setting to support more licenses

If you want to add or modify scan rules,you should edit SCAN.RE_LIST part in apps/Scan/settings.ini ,before it you should know [Regular Expression](http://docs.python.org/release/2.6.8/library/re.html#regular-expression-syntax).
