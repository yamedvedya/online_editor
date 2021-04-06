#General info:
This utility allows easy visual editing of online.xml file for Sardana. Language: Python3 + PyQt5 

#Installation:
After download you should run build.py

#Running
you can force the opening of the default library by specifying the -f (or --file) option

#Configurations libraries:
The main concept of this utility is the "configuration" - the particular set of the entries for online.xml, which can be arbitrary grouped and activated for this particular experiment.

These configurations are saved in separate .xml files. Each file can contain several configurations, so user can use one .xml file for all experiments.

The file structure is described here.  In the distributive you can find You can form it by hand, using the attached "simple_lib.xml" template, or use "Import current online.xml". 

In case of import you will obtain the library file with one configuration, with all currently used devices (commented won't be imported). You can group/organize them later with inbuilt edit options.

#Operation:
The main windows consists of two main fields:

1. configuration(s) view, where the device name, activation status, device type, sardana name and the user comments are displayed. You can add additional filed by "Select columns" menu.
2. device properties view with detailed information about the selected device
To be able to edit the configuration you should be "Superuser", the "Standard user" can only browse configurations. the user role changes in "Switch user" menu. The superuser pass is set in settings.py

##Entries types:
There are 4 types of the entries:

1. Configuration - the basic entry, can contain devices/serial devices/groups of devices/serial devices. The library file can contain several configuration, but only one can be activated
2. Group - is a container for devices/groups/serial devices which has 3 parameters - name, activation status and comment. Used to organize the structure devices and simplify the activation of several related devices. E.g. if you have a detector with positioning linear motor and you plug/unplug them always together you can combine the detector and corresponding motor entry to one group and easy add/remove them to the online.xml by activation the whole group. Additionally, you may have addition sub-groups in the group and arbitrary change their activation status. If you deactivate parent group - all sub-groups will be removed from online.xml. If you activate parent group again, that activation status of the sub-devices/groups will be restored.
3. Device (single device) - individual device, with several properties, which will be converted to the tags in the online.xml.  You can add some user comment to every device, which will be ignored during conversion.
4. Serial device - this is a device, which consist of several sub-devices with identical parameters. The individual devices can have only 5 independent parameters: name, device (tango address), sardana name, activation status, and comment. Can be useful, e.g for counters, OMS motors, e.t.c.
##Configuration view:
active devices/groups are bold, deactivated - gray italic 
*in case if group has at least one non-active device the check box displayed as partially checked
*if you deactivate group - all sub-device won't be added to the online.xml
*the device/sardana names and comments are editable by double click.
*to create/paste new device/group - right click on the parent configuration/group 
*to delete/cut/copy device/group - right click on the device 
*the devices can be ordered by drag-and-drop:
**in case you drop the device/group on the group the device will be moved to this group
**in case you drop device/group between another devices/group - the current group will be reordered
**if you drag the device with ctrl - you will make a copy of the device
##Device properties view:
Here all properties of device, selected in the tree view are displayed.

Each cell is editable by double-click. 

To add/remove properties click on the Add/remove properties button under table and use the following dialog window.
*in case you edit a serial device, the common properties will be applied to all sub-devices. The individual properties can be: name, device, sardana name.
*in case you edit group - you can only change name and comment

##Check for errors/apply configuration:
Before the selected configuration will be converted to online.xml file the following check will be performed:

*duplication of the <name>, <sardananame> tags and the tango addresses in <devices> tags for all activated devices
*all activated devices are online (by trying to execute PyTango.DeviceProxy(<device>) command
*in case if <devices> is particular attribute - the existence of the attribute will be checked
*for all measurement groups all selected devices are activated

In case you still want to apply configuration with errors you can press "Ignore" button.

You can force this check without configuration applying by clicking on the "Check configuration for error"