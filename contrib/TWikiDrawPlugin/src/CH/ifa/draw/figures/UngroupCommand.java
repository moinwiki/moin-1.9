/*
 * @(#)UngroupCommand.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import java.util.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.util.Command;

/**
 * Command to ungroup the selected figures.
 * @see GroupCommand
 */
public  class UngroupCommand extends Command {

    private DrawingView fView;

   /**
    * Constructs a group command.
    * @param name the command name
    * @param view the target view
    */
    public UngroupCommand(String name, DrawingView view) {
        super(name);
        fView = view;
    }

    public void execute() {
        FigureEnumeration selection = fView.selectionElements();
        fView.clearSelection();

        Vector parts = new Vector();
        while (selection.hasMoreElements()) {
            Figure selected = selection.nextFigure();
            Figure group = fView.drawing().orphan(selected);
            FigureEnumeration k = group.decompose();
            while (k.hasMoreElements())
                fView.addToSelection(fView.add(k.nextFigure()));
        }
        fView.checkDamage();
    }

    public boolean isExecutable() {
        return fView.selectionCount() > 0;
    }

}
