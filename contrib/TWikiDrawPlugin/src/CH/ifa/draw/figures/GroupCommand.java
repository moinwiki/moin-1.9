/*
 * @(#)GroupCommand.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.util.*;
import CH.ifa.draw.util.Command;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;

/**
 * Command to group the selection into a GroupFigure.
 *
 * @see GroupFigure
 */
public  class GroupCommand extends Command {

    private DrawingView fView;

   /**
    * Constructs a group command.
    * @param name the command name
    * @param view the target view
    */
    public GroupCommand(String name, DrawingView view) {
        super(name);
        fView = view;
    }

    public void execute() {
        Vector selected = fView.selectionZOrdered();
        Drawing drawing = fView.drawing();
        if (selected.size() > 0) {
            fView.clearSelection();
            drawing.orphanAll(selected);

            GroupFigure group = new GroupFigure();
            group.addAll(selected);
            fView.addToSelection(drawing.add(group));
        }
        fView.checkDamage();
    }

    public boolean isExecutable() {
        return fView.selectionCount() > 0;
    }

}


