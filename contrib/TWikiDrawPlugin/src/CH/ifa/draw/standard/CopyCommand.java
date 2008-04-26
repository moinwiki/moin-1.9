/*
 * @(#)CopyCommand.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.util.*;
import CH.ifa.draw.util.*;
import CH.ifa.draw.framework.*;

/**
 * Copy the selection to the clipboard.
 * @see Clipboard
 */
public class CopyCommand extends FigureTransferCommand {

   /**
    * Constructs a copy command.
    * @param name the command name
    * @param view the target view
    */
    public CopyCommand(String name, DrawingView view) {
        super(name, view);
    }

    public void execute() {
        copySelection();
    }

    public boolean isExecutable() {
        return fView.selectionCount() > 0;
    }

}


