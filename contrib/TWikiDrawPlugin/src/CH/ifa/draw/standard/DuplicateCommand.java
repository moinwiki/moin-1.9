/*
 * @(#)DuplicateCommand.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.util.*;
import CH.ifa.draw.util.*;
import CH.ifa.draw.framework.*;

/**
 * Duplicate the selection and select the duplicates.
 */
public class DuplicateCommand extends FigureTransferCommand {

   /**
    * Constructs a duplicate command.
    * @param name the command name
    * @param view the target view
    */
    public DuplicateCommand(String name, DrawingView view) {
        super(name, view);
    }

    public void execute() {
        FigureSelection selection = fView.getFigureSelection();

        fView.clearSelection();

        Vector figures = (Vector)selection.getData(FigureSelection.TYPE);
        insertFigures(figures, 10, 10);
        fView.checkDamage();
    }

    public boolean isExecutable() {
        return fView.selectionCount() > 0;
    }

}


