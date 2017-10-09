# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeodesicDensifier
                                 A QGIS plugin
 Adds vertices to geometry along geodesic lines
                              -------------------
        begin                : 2017-10-06
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Jonah Sullivan
        email                : jonahsullivan79@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
try:
    from geographiclib.geodesic import Geodesic
except ImportError:
    import sys
    import inspect
    import os
    sys.path.append(os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda: 0))))
    from geographiclib.geodesic import Geodesic
import math
from qgis.core import *
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from geodesic_densifier_dialog import GeodesicDensifierDialog
import os.path


class GeodesicDensifier:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GeodesicDensifier_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Geodesic Densifier')
        self.toolbar = self.iface.addToolBar(u'GeodesicDensifier')
        self.toolbar.setObjectName(u'GeodesicDensifier')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GeodesicDensifier', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = GeodesicDensifierDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/GeodesicDensifier/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Geodesic Densifier'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Geodesic Densifier'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # get geometry of active point layer
            layer = self.iface.activeLayer()
            in_point_list = []
            if layer:
                if layer.crs().geographicFlag():
                    layer_iter = layer.getFeatures()
                    for feature in layer_iter:
                        geom = feature.geometry()
                        if geom.type() == QGis.Point:
                            x = geom.asPoint()
                            in_point_list.append(x)
                else:
                    pass
                    # TODO add check for geogrphic CRS

            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            ellipsoid_dict = {'165' : [6378165.000, 298.3],
                              'ANS' : [6378160, 298.25],
                              'CLARKE 1858' : [6378293.645, 294.26],
                              'GRS80' : [6378137, 298.2572221],
                              'WGS84' : [6378137, 298.2572236],
                              'WGS72' : [6378135, 298.26],
                              'International 1924' : [6378388, 297]}

            # Create a geographiclib Geodesic object
            # this is the GRS80 ellipsoid used for GDA94 EPSG:4283
            geod = Geodesic(6378137.0, 1 / 298.257222100882711243)

            def densifypoints(lat1, lon1, lat2, lon2, spacing):
                # create an empty list to hold points
                dens_point_dict = {}
                # create a geographiclib line object
                line_object = geod.InverseLine(lat1, lon1, lat2, lon2)
                # set the maximum separation between densified points
                ds = spacing
                # determine how many segments there will be
                n = int(math.ceil(line_object.s13 / ds)) + 1
                # adjust the spacing distance
                ds = line_object.s13 / n
                # this variable gives each point an ID
                id = 0
                # this variable tracks how far along the line we are
                dist = 0.0
                # this variable tracks whether it is an original or densified point
                point_type = ''
                # an extra segment is needed to add half of the modulo at the front of the line
                for i in range(n + 1):
                    if i == 0 or i == n:
                        point_type = "Original"
                    else:
                        point_type = "Densified"
                    g = line_object.Position(dist, Geodesic.STANDARD)
                    # add points to the line
                    dens_point_dict[id] = [g['lon2'], g['lat2'], point_type]
                    dist += ds
                    id += 1
                return dens_point_dict

            # execute the function
            # Canberra to Darwin
            point_dict = densifypoints(in_point_list[0][1],
                                       in_point_list[0][0],
                                       in_point_list[1][1],
                                       in_point_list[1][0],
                                       900)

            # create and add to map canvas a memory layer
            point_layer = self.iface.addVectorLayer("Point", "Densified Point Layer", "memory")
            # set projection
            point_layer.setCrs(self.iface.activeLayer().crs())
            # set data provider
            pr = point_layer.dataProvider()
            # add attribute fields
            pr.addAttributes([QgsField("Sequence", QVariant.String),
                              QgsField("ID", QVariant.String),
                              QgsField("LAT", QVariant.Double),
                              QgsField("LON", QVariant.Double),
                              QgsField("PntType", QVariant.String),
                              QgsField("DensT", QVariant.String)])
            point_layer.updateFields()

            # loop through points adding geometry and attributes
            for id in point_dict.keys():
                # create a feature
                feat = QgsFeature(point_layer.pendingFields())
                # set geometry to the feature
                feat.setGeometry(QgsGeometry.fromPoint(QgsPoint(point_dict[id][0], point_dict[id][1])))
                # set attribute fields
                feat.setAttribute("Sequence", "test")
                feat.setAttribute("ID", str(id))
                feat.setAttribute("LAT", float(point_dict[id][1]))
                feat.setAttribute("LON", float(point_dict[id][0]))
                feat.setAttribute("PntType", str(point_dict[id][2]))
                feat.setAttribute("DensT", "G")
                point_layer.dataProvider().addFeatures([feat])