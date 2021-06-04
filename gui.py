#!/usr/bin/env python
'''
Contracted by Thomas Piltoff via Upwork

Generates a VLC playlist based on a user's directory
Inserts 1+ commercials from user's "commercials" folder between each video file
General usage will split an episode into 2-3 parts such that a commercial is inserted at the appropriate time
'''

from playlist_generator import *
from simpletkgui import simpleapp, simpleconfig, simpleicons, simplestyles, simpleviews, simplewidgets
import tkinter.filedialog
import os
import subprocess

__author__ = 'Michael Genson'
__copyright__ = 'Copyright (C) 2021 Michael Genson'

__license__ = 'GPL'
__version__ = '1.1.0'
__appname__ = 'TV Playlist App'

default_commercial_min = 2
default_commercial_max = 4

def set_commercial_dir(app, current_dir=None):
    '''
    Changes the directory to pull commercials from
    Saves to config file in appdata
    '''
    commercial_dir = tkinter.filedialog.askdirectory(title='Please select your commercials directory', initialdir=current_dir).replace('/', '\\')
    if commercial_dir:
        app.appconfig['_commercial_dir'] = commercial_dir
        app.appconfig.save()

    return commercial_dir

def set_vlc_dir(app, check_default=True):
    '''
    Changes the directory to open VLC
    Saves to config file in appdata
    '''
    vlc_path = None
    if check_default:
        # checks usual locations for VLC
        if os.path.exists('C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe'): vlc_path = 'C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe'
        elif os.path.exists('C:\\Program Files\\VideoLAN\\VLC\\vlc.exe'): vlc_path = 'C:\\Program Files\\VideoLAN\\VLC\\vlc.exe'
    
    # prompts user for VLC location
    if not vlc_path: vlc_path = tkinter.filedialog.askopenfilename(title='Please select playback software executable', filetypes=[('exe', '.exe')]).replace('/', '\\')

    if vlc_path:
        app.appconfig['_vlc_path'] = vlc_path
        app.appconfig.save()

    return vlc_path

def get_playlist_dir(app):
    # create directory if it doesn't exist
    playlist_dir = os.path.join(app.appconfig.working_directory, 'playlists')
    if not os.path.exists(playlist_dir): os.makedirs(playlist_dir)

    return playlist_dir

def open_playlist(app, filepath=None):
    if not filepath:
        filepath = tkinter.filedialog.askopenfilename(title='Open Playlist', initialdir=get_playlist_dir(app), filetypes=[('m3u', '.m3u')]).replace('/', '\\')
        if not filepath: return

    # get path for VLC
    vlc_path = app.appconfig['vlc_path']
    if not vlc_path:
        vlc_path = set_vlc_dir(app)
        if not vlc_path: return

    # open VLC
    subprocess.Popen([vlc_path, filepath])

def playlist_helper(app, episode_listbox):
    '''
    Builds vars for playlist generator
    Deletes old playlists
    '''

    if episode_listbox.choices == []: return

    episode_dirs = [] # converts listbox choice order into full path
    for choice in episode_listbox.choices: episode_dirs.append(episode_listbox.choices_dict[choice])

    # delete old playlist files if there are too many
    def return_playlist_created_date(filename):
        return os.path.getmtime(os.path.join(get_playlist_dir(app), filename))

    filelist = sorted(os.listdir(get_playlist_dir(app)), key=return_playlist_created_date, reverse=True)
    playlist_retention = app.appconfig['playlist_retention']
    if len(filelist) >= playlist_retention:
        for x in range(0, len(filelist) - playlist_retention + 1):
            try: os.unlink(os.path.join(get_playlist_dir(app), filelist.pop()))
            except Exception as e: print(f'Unable to remove playlist file per retention policy: {e}')

    playlist_basename = os.path.basename(episode_dirs[0])

    # generate filename from first episode_dir name
    filename_counter = 0
    filename = playlist_basename+'.m3u'
    filepath = os.path.join(get_playlist_dir(app), filename)
    while os.path.exists(filepath):
        filename_counter += 1
        filename = playlist_basename+f' ({filename_counter})'+'.m3u'
        filepath = os.path.join(get_playlist_dir(app), filename)

    # set number of commercials to insert between episode parts
    commercial_min = app.appconfig['commercial_min']
    if type(commercial_min) != int or commercial_min < 1: commercial_min = None

    if not commercial_min:
        commercial_min = 2
        app.appconfig['commercial_min'] = commercial_min
        app.appconfig.save()

    commercial_max = app.appconfig['commercial_max']
    if type(commercial_max) != int or commercial_max < 1: commercial_max = None

    if not commercial_max:
        commercial_max = default_commercial_max
        app.appconfig['commercial_max'] = commercial_max
        app.appconfig.save()

    if commercial_min <= 0: commercial_min = default_commercial_min
    if commercial_max < commercial_min: commercial_max = commercial_min

    # generates the playlist
    build_playlist(filepath, episode_dirs, app.appconfig['_commercial_dir'], commercial_min, commercial_max, __appname__, __version__)
    open_playlist(app, filepath)

def main():
    app = simpleapp.App(__appname__, minsize=(650, 400), start_hidden=True, resize=False)
    commercial_dir = app.appconfig['_commercial_dir']
    
    # first time set up
    if not commercial_dir:
        commercial_dir = set_commercial_dir(app)
    
        # if nothing is selected, quit
        if not commercial_dir: return

    # set playlist retention limit
    playlist_retention = app.appconfig['playlist_retention']
    if type(playlist_retention) != int or playlist_retention < 1: playlist_retention = None
    if not playlist_retention:
        playlist_retention = 15
        app.appconfig['playlist_retention'] = playlist_retention
        app.appconfig.save()

    # Menu Controls
    menu_options = {
        'File': {'Build New Playlist': lambda: app.change_view(playlist_builder), 'Open Playlist': lambda: open_playlist(app)},
        'Edit': {'Change Commercial Directory': lambda: set_commercial_dir(app, app.appconfig['_commercial_dir']), 'Change Playback Directory': lambda: set_vlc_dir(app, check_default=False)},
        'Goto': {'Main Menu': lambda: app.change_view(main_menu), 'Playlist Builder': lambda: app.change_view(playlist_builder),'Settings': lambda: app.change_view(settings_menu)}
    }

    menu_accelerators = [
        {
            'label': {'File': 'Build New Playlist'},
            'keys': ('Ctrl', 'N')
        },
        {
            'label': {'File': 'Open Playlist'},
            'keys': ('Ctrl', 'O')
        },
        {
            'label': {'Edit': 'Change Commercial Directory'},
            'keys': ('Ctrl', 'Alt', 'O')
        },
        {
            'label': {'Edit': 'Change Playback Directory'},
            'keys': ('Ctrl', 'Alt', 'P')
        },
        {
            'label': {'Goto': 'Main Menu'},
            'keys': ('Ctrl', 'M')
        },
        {
            'label': {'Goto': 'Playlist Builder'},
            'keys': ('Ctrl', 'Alt', 'N')
        },
        {
            'label': {'Goto': 'Settings'},
            'keys': ('Ctrl', 'Alt', 'S')
        }
    ]
    
    # Main Menu
    main_title = simpleviews.Nav(app, title=__appname__)
    main_menu = simpleviews.SimpleView(app, nav=main_title)

    # Settings Menu
    settings_title = simpleviews.Nav(app, title='Settings')
    settings_menu = simpleviews.SimpleView(app, nav=settings_title)

    # Playlist Builder
    playlist_builder_title = simpleviews.Nav(app, title='Playlist Builder')
    playlist_builder = simpleviews.GridView(app, nav=playlist_builder_title)

    nav_menu = simplewidgets.SimpleMenu(main_menu, menu_options)
    for accelerator in menu_accelerators: nav_menu.add_accelerator(**accelerator)

    # Main Menu Controls
    b_build_playlist = simplewidgets.SimpleButton(main_menu, 'Build a Playlist', lambda: app.change_view(playlist_builder))
    b_settings = simplewidgets.SimpleButton(main_menu, 'Settings', lambda: app.change_view(settings_menu))

    main_menu.build_grid({
        'row0': None,
        'row1': [b_build_playlist, b_settings],
        'row2': None,
        'row3': None
        })

    # Playlist Builder Controls
    def right_click(event):
        if not lb_episode_list.read():
            lb_episode_list.clear()
            lb_episode_list.selection_set(lb_episode_list.nearest(event.y))
            lb_episode_list.activate(lb_episode_list.nearest(event.y))

    lb_episode_list = simplewidgets.SimpleDragDropListbox(playlist_builder, {})
    app.bind('<Button-3>', right_click)

    def add_episode():
        episode_dir = tkinter.filedialog.askdirectory(title='Please select your episode directory', initialdir=app.appconfig['_last_episode_dir']).replace('/', '\\')
        episode_name = os.path.basename(episode_dir)

        episode_dirs = lb_episode_list.choices_dict
        if episode_dir and episode_dir not in episode_dirs.values():
            
            # changes episode display name if it's already taken
            if episode_name in episode_dirs:
                n = 0
                episode_name_base = episode_name
                while episode_name in episode_dirs:
                    n += 1
                    episode_name = f'{episode_name_base} ({n})'

            episode_dirs[episode_name] = episode_dir
            
            lb_episode_list.update_choices(episode_dirs)
            lb_episode_list.insert('end', episode_name)
            app.appconfig['_last_episode_dir'] = os.path.dirname(episode_dir)
            app.appconfig.save()

    def shuffle_episodes():
        episode_dirs = list(lb_episode_list.choices_dict.items())
        random.shuffle(episode_dirs)
        lb_episode_list.update_choices(dict(episode_dirs))
        
        lb_episode_list.delete(0,'end')
        for choice in lb_episode_list.choices:
            lb_episode_list.insert('end', choice)

    def remove_episode():
        if lb_episode_list.read():
            removed_episode = list(lb_episode_list.choices_dict.keys())[list(lb_episode_list.choices_dict.values()).index(lb_episode_list.read()[0])]
            lb_episode_list.delete(lb_episode_list.choices.index(removed_episode))
            del lb_episode_list.choices_dict[removed_episode]
            lb_episode_list.update_choices(lb_episode_list.choices_dict)

    b_add_episode = simplewidgets.SimpleButton(playlist_builder, '➕ Add Episode', add_episode)
    b_shuffle_episodes = simplewidgets.SimpleButton(playlist_builder, 'Shuffle Episodes', shuffle_episodes)
    b_create_playlist = simplewidgets.SimpleButton(playlist_builder, 'Create Playlist', lambda: playlist_helper(app, lb_episode_list))
    right_click_menu = simplewidgets.SimpleMenu(lb_episode_list, {'remove episode': remove_episode},context_menu=True)

    def validate_commerical_bound(bound_str, user_input):
        if not user_input: return True
        if user_input.isnumeric():
            if int(user_input) > 0:
                app.appconfig[bound_str] = int(user_input)
                app.appconfig.save()
                return True

        return False

    l_commercial_min = simplewidgets.SimpleLabel(playlist_builder, 'min number of commercials:', font=playlist_builder.style.font.body)
    l_commercial_min.configure(anchor='e')
    e_commercial_min = simplewidgets.SimpleEntry(playlist_builder)
    e_commercial_min.configure(justify='center', validate='key', validatecommand=(app.register(validate_commerical_bound), 'commercial_min', '%P'))
    if not app.appconfig['commercial_min']: app.appconfig['commercial_min'] = default_commercial_min
    e_commercial_min.change_text(app.appconfig['commercial_min'])

    l_commercial_max = simplewidgets.SimpleLabel(playlist_builder, 'max number of commercials:', font=playlist_builder.style.font.body)
    l_commercial_max.configure(anchor='e')
    e_commercial_max = simplewidgets.SimpleEntry(playlist_builder)
    e_commercial_max.configure(justify='center', validate='key', validatecommand=(app.register(validate_commerical_bound), 'commercial_max', '%P'))
    if not app.appconfig['commercial_max']: app.appconfig['commercial_max'] = default_commercial_max
    e_commercial_max.change_text(app.appconfig['commercial_max'])

    playlist_builder.add_widgets([
        ((0, 0), (4, 16), lb_episode_list),
        ((4, 0), (4, 1), b_add_episode),
        ((4, 1), (4, 1), b_shuffle_episodes),
        ((4, 3), (3, 1), l_commercial_min),
        ((7, 3), (1, 1), e_commercial_min),
        ((4, 4), (3, 1), l_commercial_max),
        ((7, 4), (1, 1), e_commercial_max),
        ((4, 15), (4, 1), b_create_playlist),
        ])

    playlist_builder.build_grid()

    # Settings Controls
    l_commercial_dir = simplewidgets.SimpleLabel(settings_menu, 'Commercials:', font=settings_menu.style.font.body)
    l_commercial_dir.configure(anchor='e')
    e_commercial_dir = simplewidgets.SimpleEntry(settings_menu, font=settings_menu.style.font.body)
    e_commercial_dir.change_text(commercial_dir)
    e_commercial_dir.disable()

    # Update settings view when directory is changed
    def _change_commercial_dir_from_settings():
        commercial_dir = set_commercial_dir(app, app.appconfig['_commercial_dir'])
        if commercial_dir:
            e_commercial_dir.enable()
            e_commercial_dir.change_text(commercial_dir)
            e_commercial_dir.disable()

    b_change_commercial_dir = simplewidgets.SimpleButton(settings_menu, 'Change Commercial Directory', _change_commercial_dir_from_settings)
    b_main_menu = simplewidgets.SimpleButton(settings_menu, 'Main Menu', lambda: app.change_view(main_menu))
    l_version_info = simplewidgets.SimpleLabel(settings_menu, f'Developed by Michael Genson - version {__version__}', font=settings_menu.style.font.body)
    l_version_info.configure(anchor='e')

    settings_menu.build_grid({
        'row1': [l_commercial_dir, e_commercial_dir, 'ext', 'ext', 'ext'],
        'row2': None,
        'row3': [b_change_commercial_dir, 'ext', 'ext', None, b_main_menu],
        'row4': None,
        'row5': [l_version_info, 'ext', 'ext', 'ext', 'ext']
        })
    
    app.change_view(main_menu)
    app.start()

if __name__ == '__main__':
    main()