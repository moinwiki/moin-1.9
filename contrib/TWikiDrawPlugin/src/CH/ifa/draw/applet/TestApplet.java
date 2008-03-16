/*
 * @(#)TestApplet.java 5.1
 *
 */

package CH.ifa.draw.applet;

import java.applet.Applet;
import java.awt.*;
import java.awt.event.*;
import java.util.*;
import java.io.*;
import java.net.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;
import CH.ifa.draw.figures.*;
import CH.ifa.draw.util.*;

//import javax.swing.*;

public class TestApplet
        extends Applet
	    implements PaletteListener {

    transient private ToolButton      fDefaultToolButton;

    private Iconkit                   fIconkit;

    private static final String       fgDrawPath = "/CH/ifa/draw/";
    public static final String        IMAGES = fgDrawPath+"images/";

    public void init() {
        fIconkit = new Iconkit(this);
/*
	ImageIcon icon = new ImageIcon( IMAGES.substring(1)+"SEL1.gif");
	JButton fred = new JButton(icon);
	add(fred);
*/
        fDefaultToolButton = new ToolButton(this, IMAGES+"SEL",
					    "Selection Tool",
					    null);
        add(fDefaultToolButton);
    }

    /**
     * Handles a user selection in the palette.
     * @see PaletteListener
     */
    public void paletteUserSelected(PaletteButton button) {
    }

    /**
     * Handles when the mouse enters or leaves a palette button.
     * @see PaletteListener
     */
    public void paletteUserOver(PaletteButton button, boolean inside) {
        if (inside)
            showStatus(((ToolButton) button).name());
        else
	    showStatus("Not over");
    }

}

