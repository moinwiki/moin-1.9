/*
 * @(#)ResourceBundleUtil.java
 *
 * Copyright (c) 1996-2009 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and
 * contributors of the JHotDraw project ("the copyright holders").
 * You may not use, copy or modify this software, except in
 * accordance with the license agreement you entered into with
 * the copyright holders. For details see accompanying license terms.
 */
package org.jhotdraw.util;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.Serializable;
import java.util.*;
import javax.swing.*;
import java.text.*;
import java.net.*;

/**
 * This is a convenience wrapper for accessing resources stored in a
 * ResourceBundle.
 * <p>
 * <b>Placeholders</b><br>
 * On top of the functionality provided by ResourceBundle, a property value
 * can include text from another property, by specifying the desired
 * property name between <code>"${"</code> and <code>"}"</code>.
 * <p>
 * For example, if there is a {@code "imagedir"} property with the value
 * {@code "/org/jhotdraw/undo/images"}, then this could be used in an attribute
 * like this: <code>${imagedir}/editUndo.png</code>. This is resolved at run-time
 * as {@code /org/jhotdraw/undo/images/editUndo.png}.
 * <p>
 * Property names in placeholders can contain modifiers. Modifiers are written
 * between @code "[$"} and {@code "]"}. Each modifier has a fallback chain.
 * <p>
 * For example, if the property name modifier {@code "os"} has the value "win",
 * and its fallback chain is {@code "mac","default"}, then the property name
 * <code>${preferences.text.[$os]}</code> is first evaluted to {@code
 * preferences.text.win},  and - if no property with this name exists -
 * it is evaluated to {@code preferences.text.mac}, and then to
 * {@code preferences.text.default}.
 * <p>
 * The property name modifier "os" is defined by default. It can assume the
 * values "win", "mac" and "other". Its fallback chain is "default".
 *
 * @author  Werner Randelshofer, Staldenmattweg 2, CH-6405 Immensee, Switzerland
 * @version $Id: ResourceBundleUtil.java 541 2009-07-04 14:24:31Z rawcoder $
 */
public class ResourceBundleUtil implements Serializable {

    /** The wrapped resource bundle. */
    private transient ResourceBundle resource;
    /** The locale. */
    private Locale locale;
    /** The base class */
    private Class baseClass = getClass();
    /**
     * The base name of the resource bundle.
     */
    private String baseName;
    /**
     * The global verbose property.
     */
    private static boolean isVerbose = false;
    /**
     * The global map of property name modifiers.
     * The key of this map is the name of the property name modifier,
     * the value of this map is a fallback chain.
     */
    private static HashMap<String, String[]> propertyNameModifiers = new HashMap<String, String[]>();


    static {
        String osName = System.getProperty("os.name").toLowerCase();
        String os;
        if (osName.startsWith("mac os x")) {
            os = "mac";
        } else if (osName.startsWith("windows")) {
            os = "win";
        } else {
            os = "other";
        }
        propertyNameModifiers.put("os", new String[]{os, "default"});
    }

    /**
     * Creates a new ResouceBundleUtil which wraps
     * the provided resource bundle.
     */
    public ResourceBundleUtil(String baseName, Locale locale) {
        this.locale = locale;
        this.baseName = baseName;
        this.resource = ResourceBundle.getBundle(baseName, locale);
    }

    /**
     * Returns the wrapped resource bundle.
     * @return The wrapped resource bundle.
     */
    public ResourceBundle getWrappedBundle() {
        return resource;
    }

    /**
     * Get a String from the ResourceBundle.
     * <br>Convenience method to save casting.
     *
     * @param key The key of the property.
     * @return The value of the property. Returns the key
     *          if the property is missing.
     */
    public String getString(String key) {
        try {
            String value = getStringRecursive(key);
            // System.out.println("ResourceBundleUtil "+baseName+" get("+key+"):"+value);
            return value;
        } catch (MissingResourceException e) {
            // System.out.println("ResourceBundleUtil "+baseName+" get("+key+"):***MISSING***");
            if (isVerbose) {
                System.err.println("Warning ResourceBundleUtil[" + baseName + "] \"" + key + "\" not found.");
            //e.printStackTrace();
            }
            return key;
        }
    }

    /**
     * Recursive part of the getString method.
     *
     * @param key
     * @return
     * @throws java.util.MissingResourceException
     */
    private String getStringRecursive(String key) throws MissingResourceException {
        String value = resource.getString(key);

        // Substitute placeholders in the value
        for (int p1 = value.indexOf("${"); p1 != -1; p1 = value.indexOf("${")) {
            int p2 = value.indexOf('}', p1 + 2);
            if (p2 == -1) {
                break;
            }

            String placeholderKey = value.substring(p1 + 2, p2);
            ArrayList<String> fallbackKeys = new ArrayList<String>();
            generateFallbackKeys(placeholderKey, fallbackKeys);

            boolean resourceFound = false;
            for (String fk : fallbackKeys) {
                try {
                    value = value.substring(0, p1) + getStringRecursive(fk) + value.substring(p2 + 1);
                    resourceFound = true;
                    break;
                } catch (MissingResourceException e) {
                }
            }
            if (resourceFound == false) {
                throw new MissingResourceException("Resource not found.", baseName, key);
            }
        }

        return value;
    }

    /**
     * Generates fallback keys by processing all property name modifiers
     * in the key.
     */
    private void generateFallbackKeys(String key, ArrayList<String> fallbackKeys) {
        int p1 = key.indexOf("[$");
        if (p1 == -1) {
            fallbackKeys.add(key);
        } else {
            int p2 = key.indexOf(']', p1 + 2);
            if (p2 == -1) {
                return;
            }
            String modifierKey = key.substring(p1 + 2, p2);
            String[] modifierValues = propertyNameModifiers.get(modifierKey);
            if (modifierValues == null) {
                modifierValues = new String[]{"default"};
            }
            for (String mv : modifierValues) {
                generateFallbackKeys(key.substring(0, p1) + mv + key.substring(p2 + 1), fallbackKeys);
            }
        }
    }

    /**
     * Returns a formatted string using javax.text.MessageFormat.
     * @param key
     * @param arguments
     * @return formatted String
     */
    public String getFormatted(String key, Object... arguments) {
        return MessageFormat.format(getString(key), arguments);
    }

    /**
     * Returns a formatted string using java.util.Formatter().
     * @param key
     * @param arguments
     * @return formatted String
     */
    public String format(String key, Object... arguments) {
        //return String.format(resource.getLocale(), getString(key), arguments);
        return new Formatter(resource.getLocale()).format(getString(key), arguments).toString();
    }

    /**
     * Get an Integer from the ResourceBundle.
     * <br>Convenience method to save casting.
     *
     * @param key The key of the property.
     * @return The value of the property. Returns -1
     *          if the property is missing.
     */
    public Integer getInteger(String key) {
        try {
            return Integer.valueOf(getStringRecursive(key));
        } catch (MissingResourceException e) {
            if (isVerbose) {
                System.err.println("Warning ResourceBundleUtil[" + baseName + "] \"" + key + "\" not found.");
            //e.printStackTrace();
            }
            return new Integer(-1);
        }
    }

    /**
     * Get an image icon from the ResourceBundle.
     * <br>Convenience method .
     *
     * @param key The key of the property. This method appends ".icon" to the key.
     * @return The value of the property. Returns null
     *          if the property is missing.
     */
    public ImageIcon getIconProperty(String key, Class baseClass) {
        try {


            String rsrcName = getStringRecursive(key + ".icon");

            if (rsrcName.equals("")) {
                return null;
            }

            URL url = baseClass.getResource(rsrcName);
            if (isVerbose && url == null) {
                System.err.println("Warning ResourceBundleUtil[" + baseName + "].getIconProperty \"" + key + ".icon\" resource:"+rsrcName+" not found.");
            }
            return (url == null) ? null : new ImageIcon(url);
        } catch (MissingResourceException e) {
            if (isVerbose) {
                System.err.println("Warning ResourceBundleUtil[" + baseName + "].getIconProperty \"" + key + ".icon\" not found.");
            //e.printStackTrace();
            }
            return null;
        }
    }

    /**
     * Get a Mnemonic from the ResourceBundle.
     * <br>Convenience method.
     *
     * @param key The key of the property.
     * @return The first char of the value of the property.
     *          Returns '\0' if the property is missing.
     */
    public char getMnemonic(String key) {
        String s = getStringRecursive(key);
        return (s == null || s.length() == 0) ? '\0' : s.charAt(0);
    }

    /**
     * Gets a char for a JavaBeans "mnemonic" property from the ResourceBundle.
     * <br>Convenience method.
     *
     * @param key The key of the property. This method appends ".mnemonic" to the key.
     * @return The first char of the value of the property.
     *          Returns '\0' if the property is missing.
     */
    public char getMnemonicProperty(String key) {
        String s;
        try {
            s = getStringRecursive(key + ".mnemonic");
        } catch (MissingResourceException e) {
            if (isVerbose) {
                System.err.println("Warning ResourceBundleUtil[" + baseName + "] \"" + key + ".mnemonic\" not found.");
            //e.printStackTrace();
            }
            s = null;
        }
        return (s == null || s.length() == 0) ? '\0' : s.charAt(0);
    }

    /**
     * Get a String for a JavaBeans "toolTipText" property from the ResourceBundle.
     * <br>Convenience method.
     *
     * @param key The key of the property. This method appends ".toolTipText" to the key.
     * @return The ToolTip. Returns null if no tooltip is defined.
     */
    public String getToolTipTextProperty(String key) {
        try {
            String value = getStringRecursive(key + ".toolTipText");
            return value;
        } catch (MissingResourceException e) {
            if (isVerbose) {
                System.err.println("Warning ResourceBundleUtil[" + baseName + "] \"" + key + ".toolTipText\" not found.");
            //e.printStackTrace();
            }
            return null;
        }

    }

    /**
     * Get a String for a JavaBeans "text" property from the ResourceBundle.
     * <br>Convenience method.
     *
     * @param key The key of the property. This method appends ".text" to the key.
     * @return The ToolTip. Returns null if no tooltip is defined.
     */
    public String getTextProperty(String key) {
        try {
            String value = getStringRecursive(key + ".text");
            return value;
        } catch (MissingResourceException e) {
            if (isVerbose) {
                System.err.println("Warning ResourceBundleUtil[" + baseName + "] \"" + key + ".text\" not found.");
            //e.printStackTrace();
            }
            return null;
        }

    }

    /**
     * Get a KeyStroke from the ResourceBundle.
     * <BR>Convenience method.
     *
     * @param key The key of the property.
     * @return <code>javax.swing.KeyStroke.getKeyStroke(value)</code>.
     *          Returns null if the property is missing.
     */
    public KeyStroke getKeyStroke(String key) {
        KeyStroke ks = null;
        try {
            String s = getStringRecursive(key);
            ks = (s == null) ? (KeyStroke) null : KeyStroke.getKeyStroke(s);
        } catch (NoSuchElementException e) {
        }
        return ks;
    }

    /**
     * Gets a KeyStroke for a JavaBeans "accelerator" property from the ResourceBundle.
     * <BR>Convenience method.
     *
     * @param key The key of the property. This method adds ".accelerator" to the key.
     * @return <code>javax.swing.KeyStroke.getKeyStroke(value)</code>.
     *          Returns null if the property is missing.
     */
    public KeyStroke getAcceleratorProperty(String key) {
        KeyStroke ks = null;
        try {
            String s;
            s = getStringRecursive(key + ".accelerator");
            ks = (s == null) ? (KeyStroke) null : KeyStroke.getKeyStroke(s);
        } catch (MissingResourceException e) {
            if (isVerbose) {
                System.err.println("Warning ResourceBundleUtil[" + baseName + "] \"" + key + ".accelerator\" not found.");
            //e.printStackTrace();
            }
        } catch (NoSuchElementException e) {
        }
        return ks;
    }

    /**
     * Get the appropriate ResourceBundle subclass.
     *
     * @see java.util.ResourceBundle
     */
    public static ResourceBundleUtil getBundle(String baseName)
            throws MissingResourceException {
        return getBundle(baseName, LocaleUtil.getDefault());
    }

    public void setBaseClass(Class baseClass) {
        this.baseClass = baseClass;
    }

    public Class getBaseClass() {
        return baseClass;
    }

    public void configureAction(Action action, String argument) {
        configureAction(action, argument, getBaseClass());
    }

    public void configureAction(Action action, String argument, Class baseClass) {
        action.putValue(Action.NAME, getTextProperty(argument));
        String shortDescription = getToolTipTextProperty(argument);
        if (shortDescription != null && shortDescription.length() > 0) {
            action.putValue(Action.SHORT_DESCRIPTION, shortDescription);
        }
        action.putValue(Action.ACCELERATOR_KEY, getAcceleratorProperty(argument));
        action.putValue(Action.MNEMONIC_KEY, new Integer(getMnemonicProperty(argument)));
        action.putValue(Action.SMALL_ICON, getIconProperty(argument, baseClass));
    }

    public void configureButton(AbstractButton button, String argument) {
        configureButton(button, argument, getBaseClass());
    }

    public void configureButton(AbstractButton button, String argument, Class baseClass) {
        button.setText(getTextProperty(argument));
        //button.setACCELERATOR_KEY, getAcceleratorProperty(argument));
        //action.putValue(Action.MNEMONIC_KEY, new Integer(getMnemonicProperty(argument)));
        button.setIcon(getIconProperty(argument, baseClass));
        button.setToolTipText(getToolTipTextProperty(argument));
    }

    public void configureToolBarButton(AbstractButton button, String argument) {
        configureToolBarButton(button, argument, getBaseClass());
    }

    public void configureToolBarButton(AbstractButton button, String argument, Class baseClass) {
        Icon icon = getIconProperty(argument, baseClass);
        if (icon != null) {
            button.setIcon(getIconProperty(argument, baseClass));
            button.setText(null);
        } else {
            button.setIcon(null);
            button.setText(getTextProperty(argument));
        }
        button.setToolTipText(getToolTipTextProperty(argument));
    }

    public void configureMenu(JMenuItem menu, String argument) {
        menu.setText(getTextProperty(argument));
        if (!(menu instanceof JMenu)) {
            menu.setAccelerator(getAcceleratorProperty(argument));
        }
        menu.setMnemonic(getMnemonicProperty(argument));
        menu.setIcon(getIconProperty(argument, baseClass));
    }

    public JMenuItem createMenuItem(Action a, String baseName) {
        JMenuItem mi = new JMenuItem();
        mi.setAction(a);
        configureMenu(mi, baseName);
        return mi;
    }

    /**
     * Get the appropriate ResourceBundle subclass.
     *
     * @see java.util.ResourceBundle
     */
    public static ResourceBundleUtil getBundle(String baseName, Locale locale)
            throws MissingResourceException {
        ResourceBundleUtil r;
        r = new ResourceBundleUtil(baseName,locale);
        return r;
    }

    @Override
    public String toString() {
        return super.toString() + "[" + baseName+", "+resource + "]";
    }

    public static void setVerbose(boolean newValue) {
        isVerbose = newValue;
    }

    public static boolean isVerbose() {
        return isVerbose;
    }

    /**
     * Puts a property name modifier along with a fallback chain.
     *
     * @param name The name of the modifier.
     * @param fallbackChain The fallback chain of the modifier.
     */
    public static void putPropertyNameModifier(String name, String... fallbackChain) {
        propertyNameModifiers.put(name, fallbackChain);
    }

    /**
     * Removes a property name modifier.
     */
    public static void removePropertyNameModifier(String name) {
        propertyNameModifiers.remove(name);
    }

    /** Read object from ObjectInputStream and re-establish ResourceBundle. */
    private void readObject(ObjectInputStream in) throws IOException, ClassNotFoundException {
        // our "pseudo-constructor"
        in.defaultReadObject();
        // re-establish the "resource" variable
        this.resource = ResourceBundle.getBundle(baseName, locale);
    }
}
