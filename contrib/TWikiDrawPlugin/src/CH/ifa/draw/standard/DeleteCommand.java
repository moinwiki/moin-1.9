/*
 * @(#)DeleteCommand.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.util.*;
import CH.ifa.draw.util.Command;
import CH.ifa.draw.framework.*;

/**
 * Command to delete the selection.
 */
public class DeleteCommand extends FigureTransferCommand {

   /**
    * Constructs a delete command.
    * @param name the command name
    * @param view the target view
    */
    public DeleteCommand(String name, DrawingView view) {
        super(name, view);
    }

    public void execute() {
        deleteSelection();
        fView.checkDamage();
    }

    public boolean isExecutable() {
        return fView.selectionCount() > 0;
    }

}


