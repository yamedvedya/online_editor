# General info:
This utility simplifies online.xml handling .

Full instruction can be found here: https://confluence.desy.de/display/FSP23/Onlinexml+Editor

# Running
you can force the opening of the default library by specifying the -f (or --file) option

# Configurations libraries:
The main concept of this utility is the "configuration" - the particular set of the entries for online.xml, which can be arbitrary grouped and activated for this particular experiment.

These configurations are saved in separate .xml files. Each file can contain several configurations, so user can use one .xml file for all experiments.
Current configuration always saved in ~/.onlinexml_editor/default.xml file.

# Operation:
The main windows consists of two main fields:

1. configuration(s) view, where the device name, activation status, device type, sardana name and the user comments are displayed. You can add additional filed by "Select columns" menu.
2. device properties view with detailed information about the selected device
To be able to edit the configuration you should be "Superuser", the "Standard user" can only browse configurations. the user role changes in "Switch user" menu. The superuser pass is set in settings.py

## Entries types:
There are 4 types of the entries:

1. Configuration - the basic entry, can contain devices/serial devices/groups of devices/serial devices. The library file can contain several configuration, but only one can be activated
2. Group - is a container for devices/groups/serial devices which has 3 parameters - name, activation status and comment. Used to organize the structure devices and simplify the activation of several related devices. E.g. if you have a detector with positioning linear motor and you plug/unplug them always together you can combine the detector and corresponding motor entry to one group and easy add/remove them to the online.xml by activation the whole group. Additionally, you may have addition sub-groups in the group and arbitrary change their activation status. If you deactivate parent group - all sub-groups will be removed from online.xml. If you activate parent group again, that activation status of the sub-devices/groups will be restored.
3. Device (single device) - individual device, with several properties, which will be converted to the tags in the online.xml.  You can add some user comment to every device, which will be ignored during conversion.
4. Serial device - this is a device, which consist of several sub-devices with identical parameters. The individual devices can have only 5 independent parameters: name, device (tango address), sardana name, activation status, and comment. Can be useful, e.g for counters, OMS motors, e.t.c.
## Configuration view:
active devices/groups are bold, deactivated - gray italic 
* in case if group has at least one non-active device the check box displayed as partially checked
* if you deactivate group - all sub-device won't be added to the online.xml
* the device/sardana names and comments are editable by double click.
* to create/paste new device/group - right click on the parent configuration/group 
* to delete/cut/copy device/group - right click on the device 
* the devices can be ordered by drag-and-drop:
** in case you drop the device/group on the group the device will be moved to this group
** in case you drop device/group between another devices/group - the current group will be reordered
** if you drag the device with ctrl - you will make a copy of the device
## Device properties view:
Here all properties of device, selected in the tree view are displayed.

Each cell is editable by double-click. 

To add/remove properties click on the Add/remove properties button under table and use the following dialog window.
* in case you edit a serial device, the common properties will be applied to all sub-devices. The individual properties can be: name, device, sardana name.
* in case you edit group - you can only change name and comment

## Check for errors/apply configuration:
Before the selected configuration will be converted to online.xml file the following check will be performed:

* duplication of the <name>, <sardananame> tags and the tango addresses in <devices> tags for all activated devices
* all activated devices are online (by trying to execute PyTango.DeviceProxy(<device>) command
* in case if <devices> is particular attribute - the existence of the attribute will be checked
* for all measurement groups all selected devices are activated

In case you still want to apply configuration with errors you can press "Ignore" button.

You can force this check without configuration applying by clicking on the "Check configuration for error"

# Configurations file
The configuration file is a .xml file with one root element:

```xml
<library>
</library>
```

Every file can contain several configurations. Each configuration should have 3 attributes: name, active- its activation status (can be "yes" or "no"), and comment:
```xml
<configuration active="yes" comment="" name="default">
</configuration>
```

In contrast to the online.xml these  3 attributes: name, active, comment should be presented in every element 
The single device entry is very similar to the online.xml entry:
```xml
<single_device active="yes" comment="" name="dcmbragg">
   <device>dcmbragg/dcmtsai/axis1</device>
   <type>type_tango</type>
   <module>motor_tango</module>
   <control>tango</control>
   <hostname>hasep23oh:10000</hostname>
</single_device>
```


All devices can be organize by groups:
```xml
<group active="yes" comment="" name="OH">
</group>
```


Additionally there is a concept of "serial device".  This is a series of devices, where only <name>, <sardananame> and <device> tags are different:
```xml
<serial_device active="yes" comment="" name="Slit 2">
   <type>stepping_motor</type>
   <module>oms58</module>
   <control>tango</control>
   <hostname>hasepfe:10000</hostname>
   <single_device active="yes" comment="" name="ps2vg">
      <device>p23/motor/fe.19</device>
   </single_device>
   <single_device active="yes" comment="" name="ps2v">
      <device>p23/motor/fe.20</device>
   </single_device>
   <single_device active="yes" comment="" name="ps2l">
      <device>p23/motor/fe.21</device>
   </single_device>
   <single_device active="yes" comment="" name="ps2r">
      <device>p23/motor/fe.22</device>
   </single_device>
</serial_device>
```