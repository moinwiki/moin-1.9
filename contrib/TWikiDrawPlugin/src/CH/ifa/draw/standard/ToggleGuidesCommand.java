/*
 * @(#)ToggleGuidesCommand.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.util.*;
import java.awt.*;
import CH.ifa.draw.util.*;
import CH.ifa.draw.framework.*;

/**
 * Command to insert the clipboard into the drawing.
 * @see Clipboard
 */
public class ToggleGuidesCommand extends Command {
    private DrawingView fView;

   /**
    * @param name the command name
    * @param image the pathname of the image
    * @param view the target view
    */
    public ToggleGuidesCommand(String name, DrawingView view) {
        super(name);
	fView = view;
    }

    public void execute() {
	fView.enableGuides(!fView.guidesEnabled());
	((Component)fView).repaint();
    }
}


