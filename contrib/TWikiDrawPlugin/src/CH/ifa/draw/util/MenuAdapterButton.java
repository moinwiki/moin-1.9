/*
 * @(#)CommandChoice.java 5.1
 *
 */

package CH.ifa.draw.util;

import java.awt.*;
import java.awt.event.*;
import java.util.*;

/**
 * A Command enabled menu. Selecting an item executes the
 * corresponding command.
 *
 * @see Command
 */

public class MenuAdapterButton
        extends Button implements ActionListener {

    PopupMenu menu;

    public MenuAdapterButton(PopupMenu m) {
	super(m.getLabel());
	menu = m;
	addActionListener(this);
    }

    public void actionPerformed(ActionEvent e) {
	menu.show(this, 0, 0);
    }
}


