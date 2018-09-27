# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NeatMap
                                 A QGIS plugin
 A simple QGIS python plugin for building tidy cities.
                             -------------------
        begin                : 2016-11-30
        copyright            : (C) 2016 by IGN
        email                : julien.perret@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load NeatMap class from file NeatMap.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .tidy_city import TidyCity
    return TidyCity(iface)
