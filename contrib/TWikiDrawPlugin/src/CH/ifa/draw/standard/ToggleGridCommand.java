/*
 * @(#)ToggleGridCommand.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.util.*;
import java.awt.Point;
import CH.ifa.draw.util.Command;
import CH.ifa.draw.framework.*;

/**
 * A command to toggle the snap to grid behavior.
 */
public class ToggleGridCommand extends Command {

    private DrawingView fView;
    private Point fGrid;

   /**
    * Constructs a toggle grid command.
    * @param name the command name
    * @param image the pathname of the image
    * @param grid the grid size. A grid size of 1,1 turns grid snapping off.
    */
    public ToggleGridCommand(String name, DrawingView view, Point grid) {
        super(name);
        fView = view;
        fGrid = new Point(grid.x, grid.y);
    }

    public void execute() {
        PointConstrainer grid = fView.getConstrainer();
        if (grid != null) {
            fView.setConstrainer(null);
        }
        else {
            fView.setConstrainer(new GridConstrainer(fGrid.x, fGrid.y));
        }
    }
}


