# -*- coding: utf-8 -*-
"""
Created on Sun May 12 20:46:26 2019
Modified on Sun Jan 17 2021

@author: syuntoku
@author: spacemaster85
@author: kvkpraneeth
"""

import adsk, os, re
from xml.etree.ElementTree import Element, SubElement
from . import Link, Joint
from ..utils import utils

def write_link_urdf(joints_dict, repo, links_xyz_dict, file_name, inertial_dict, material_dict):
    """
    Write links information into urdf "repo/file_name"
    
    
    Parameters
    ----------
    joints_dict: dict
        information of the each joint
    repo: str
        the name of the repository to save the xml file
    links_xyz_dict: vacant dict
        xyz information of the each link
    file_name: str
        urdf full path
    inertial_dict:
        information of the each inertial
    material_dict:
        information of the each inertial    
    Note
    ----------
    In this function, links_xyz_dict is set for write_joint_tran_urdf.
    The origin of the coordinate of center_of_mass is the coordinate of the link
    """
    
    
    
    with open(file_name, mode='a') as f:
        # for base_link
        center_of_mass = inertial_dict['base_link']['center_of_mass']
        link = Link.Link(name='base_link', xyz=[0,0,0], 
            center_of_mass=center_of_mass, repo=repo,
            mass=inertial_dict['base_link']['mass'],
            inertia_tensor=inertial_dict['base_link']['inertia'],
            material = material_dict['base_link']['material'])
        links_xyz_dict[link.name] = link.xyz
        link.make_link_xml()
        f.write(link.link_xml)
        f.write('\n')

        # others
        for joint in joints_dict:
            num_child = 0
            for joint_search in joints_dict:
                if joints_dict[joint]['child'] == joints_dict[joint_search]['child']:
                    num_child += 1

            if num_child > 1:
                app = adsk.core.Application.get()
                ui = app.userInterface
                ui.messageBox("Component %s with more than one child connection.\
                     \nThis mostly happens when you connect several subcomponents to different parents.\
                      \nBe aware to threat nested componets as a singel component!"
                % (joints_dict[joint]['child']), "Error!")
                quit()
            else: 
                name = re.sub('[ :()]', '_', joints_dict[joint]['child'])
                center_of_mass = \
                    [ i-j for i, j in zip(inertial_dict[name]['center_of_mass'], joints_dict[joint]['xyz'])]
                link = Link.Link(name=name, xyz=joints_dict[joint]['xyz'],\
                    center_of_mass=center_of_mass,\
                    repo=repo, mass=inertial_dict[name]['mass'],\
                    inertia_tensor=inertial_dict[name]['inertia'],
                    material = material_dict[name]['material'])
                links_xyz_dict[link.name] = link.xyz            
                link.make_link_xml()
                f.write(link.link_xml)
                f.write('\n')


def write_joint_urdf(joints_dict, repo, links_xyz_dict, file_name):
    """
    Write joints and transmission information into urdf "repo/file_name"
    
    
    Parameters
    ----------
    joints_dict: dict
        information of the each joint
    repo: str
        the name of the repository to save the xml file
    links_xyz_dict: dict
        xyz information of the each link
    file_name: str
        urdf full path
    """
    
    with open(file_name, mode='a') as f:
        for j in joints_dict:
            parent = joints_dict[j]['parent']
            child = joints_dict[j]['child']
            joint_type = joints_dict[j]['type']
            upper_limit = joints_dict[j]['upper_limit']
            lower_limit = joints_dict[j]['lower_limit']
            try:
                xyz = [round(p-c, 6) for p, c in \
                    zip(links_xyz_dict[parent], links_xyz_dict[child])]  # xyz = parent - child
            except KeyError as ke:
                app = adsk.core.Application.get()
                ui = app.userInterface
                ui.messageBox("There seems to be an error with the connection between\n\n%s\nand\n%s\n\nCheck \
whether the connections\nparent=component2=%s\nchild=component1=%s\nare correct or if you need \
to swap component1<=>component2"
                % (parent, child, parent, child), "Error!")
                quit()
                
            joint = Joint.Joint(name=j, joint_type = joint_type, xyz=xyz, \
            axis=joints_dict[j]['axis'], parent=parent, child=child, \
            upper_limit=upper_limit, lower_limit=lower_limit)
            joint.make_joint_xml()
            f.write(joint.joint_xml)
            f.write('\n')

def write_gazebo_endtag(file_name):
    """
    Write about gazebo_plugin and the </robot> tag at the end of the urdf
    
    
    Parameters
    ----------
    file_name: str
        urdf full path
    """
    with open(file_name, mode='a') as f:
        f.write('</robot>\n')
        

def write_urdf(joints_dict, links_xyz_dict, inertial_dict, material_dict, package_name, robot_name, save_dir):
    try: os.mkdir(save_dir + '/urdf')
    except: pass 

    file_name = save_dir + '/urdf/' + robot_name.lower() + '.xacro'  # the name of urdf file
    repo = package_name + '/meshes/'  # the repository of binary stl files
    with open(file_name, mode='w') as f:

        f.write('<?xml version="1.0" ?>\n')
        f.write('<robot name="{}" xmlns:xacro="http://www.ros.org/wiki/xacro">\n'.format(robot_name))
        f.write('\n')
        f.write('<xacro:include filename="$(find {})/urdf/materials.xacro" />'.format(package_name))
        f.write('\n')

    write_link_urdf(joints_dict, repo, links_xyz_dict, file_name, inertial_dict, material_dict)
    write_joint_urdf(joints_dict, repo, links_xyz_dict, file_name)
    write_gazebo_endtag(file_name)

def write_materials_xacro(color_dict, robot_name, save_dir):
    try: os.mkdir(save_dir + '/urdf')
    except: pass  

    file_name = save_dir + '/urdf/materials.xacro'  # the name of urdf file
    with open(file_name, mode='w') as f:
        f.write('<?xml version="1.0" ?>\n')
        f.write('<robot name="{}" xmlns:xacro="http://www.ros.org/wiki/xacro" >\n'.format(robot_name))
        f.write('\n')
        for color in color_dict:
            f.write(f'<material name="{color}">\n')
            f.write(f'  <color rgba="{color_dict[color]}"/>\n')
            f.write('</material>\n')
        f.write('\n')
        f.write('</robot>\n')
