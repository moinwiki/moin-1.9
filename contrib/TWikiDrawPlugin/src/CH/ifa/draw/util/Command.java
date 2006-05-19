/*
 * @(#)Command.java 5.1
 *
 */

package CH.ifa.draw.util;

import java.awt.*;
import java.util.*;

/**
 * Commands encapsulate an action to be executed. Commands have
 * a name and can be used in conjunction with <i>Command enabled</i>
 * ui components.
 * <hr>
 * <b>Design Patterns</b><P>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld010.htm>Command</a></b><br>
 * Command is a simple instance of the command pattern without undo
 * support.
 * <hr>
 *
 * @see CommandButton
 * @see CommandMenu
 * @see CommandChoice
 */
public abstract class Command {

    private String  fName;

    /**
     * Constructs a command with the given name.
     */
    public Command(String name) {
        fName = name;
    }

    /**
     * Executes the command.
     */
    public abstract void execute();

    /**
     * Tests if the command can be executed.
     */
    public boolean isExecutable() {
        return true;
    }

    /**
     * Gets the command name.
     */
    public String name() {
        return fName;
    }
}
