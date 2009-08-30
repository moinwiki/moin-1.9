/*
 * @(#)ColorMap.java 5.1
 *
 */

package CH.ifa.draw.util;

import java.awt.Color;
import java.util.*;

class ColorEntry {
    public String 	fName;
    public Color 	fColor;

    ColorEntry(String name, Color color) {
	fColor = color;
	fName = name;
    }
}

/**
 * A map that is filled with some standard colors. The colors
 * can be looked up by name or index.
 *
 */

public  class ColorMap
    extends Object {

    static ColorEntry defaultMap[] = {
	// there is no support for alpha values so we use a special value
	// to represent a transparent color
	new ColorEntry("None",          new Color(0xFFC79E)),
	new ColorEntry("White",         Color.white),
	new ColorEntry("Light Gray",    Color.lightGray),
	new ColorEntry("Gray",          Color.gray),
	new ColorEntry("Dark Gray",     Color.darkGray),
	new ColorEntry("Black",         Color.black),
	new ColorEntry("Blue",          Color.blue),
	new ColorEntry("Cyan",		Color.cyan),
	new ColorEntry("Green",         Color.green),
	new ColorEntry("Magenta",       Color.magenta),
	new ColorEntry("Orange",        Color.orange),
	new ColorEntry("Pink",          Color.pink),
	new ColorEntry("Red",           Color.red),
	new ColorEntry("Yellow",        Color.yellow),
    };

    static ColorMap colorMap = null;

    Vector fMap = null;

    ColorMap() {
	fMap = new Vector();
	for (int i = 0; i < defaultMap.length; i++)
	    addColor(defaultMap[i]);
    }

    public static void reset() {
	colorMap = null;
    }

    public static ColorMap getColorMap() {
	if (colorMap == null)
	    colorMap = new ColorMap();
	return colorMap;
    }

    public int size() {
	return fMap.size();
    }

    private void addColor(ColorEntry color) {
	fMap.addElement(color);
    }

    public void addColor(String name, Color colour) {
	addColor(new ColorEntry(name, colour));
    }

    public Color color(int index) {
	if (index < size() && index >= 0)
	    return ((ColorEntry)fMap.elementAt(index)).fColor;
	
	throw new ArrayIndexOutOfBoundsException("Color index: " + index);
    }

    public Color color(String name) {
	Enumeration e = fMap.elements();
	while (e.hasMoreElements()) {
	    ColorEntry ce = (ColorEntry)e.nextElement();
            if (ce.fName.equals(name))
                return ce.fColor;
	}
	return Color.black;
    }

    public String name(int index) {
	if (index < size() && index >= 0)
	    return ((ColorEntry)fMap.elementAt(index)).fName;
	
	throw new ArrayIndexOutOfBoundsException("Color index: " + index);
    }

    public int colorIndex(Color color) {
	Enumeration e = fMap.elements();
	int i = 0;
	while (e.hasMoreElements()) {
	    ColorEntry ce = (ColorEntry)e.nextElement();
            if (ce.fColor.equals(color))
                return i;
	    i++;
	}
        return 0;
    }

    public boolean isTransparent(Color color) {
        return color.equals(color("None"));
    }
}
