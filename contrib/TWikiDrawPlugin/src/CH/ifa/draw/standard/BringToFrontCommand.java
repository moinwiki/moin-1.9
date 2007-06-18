/*
 * @(#)BringToFrontCommand.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.util.*;
import CH.ifa.draw.util.Command;
import CH.ifa.draw.framework.*;

/**
 * BringToFrontCommand brings the selected figures in the front of
 * the other figures.
 *
 * @see SendToBackCommand
 */
public class BringToFrontCommand
       extends Command {

    private DrawingView fView;

   /**
    * Constructs a bring to front command.
    * @param name the command name
    * @param view the target view
    */
    public BringToFrontCommand(String name, DrawingView view) {
        super(name);
        fView = view;
    }

    public void execute() {
       FigureEnumeration k = new FigureEnumerator(fView.selectionZOrdered());
       while (k.hasMoreElements()) {
            fView.drawing().bringToFront(k.nextFigure());
        }
        fView.checkDamage();
    }

    public boolean isExecutable() {
        return fView.selectionCount() > 0;
    }
}


