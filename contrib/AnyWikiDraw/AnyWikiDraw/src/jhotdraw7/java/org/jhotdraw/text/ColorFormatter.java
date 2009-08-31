/*
 * @(#)ColorFormatter.java
 * 
 * Copyright (c) 2009 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 * 
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.text;

import java.awt.Color;
import java.text.ParseException;
import java.util.prefs.Preferences;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.swing.JFormattedTextField.AbstractFormatterFactory;
import javax.swing.text.DefaultFormatter;
import javax.swing.text.DefaultFormatterFactory;
import org.jhotdraw.util.prefs.PreferencesUtil;

/**
 * {@code ColorFormatter} is used to format colors into a textual representation
 * which can be edited in an entry field.
 * <p>
 * The following formats are supported:
 * <ul>
 * <li><b>Format.RGB_HEX - {@code #rrggbb} or  {@code #rgb} .</b>
 * If 6 digits are entered, each pair of hexadecimal digits, in the range 0
 * to F, represents one sRGB color component in the order red, green and blue.
 * The digits A to F may be in either uppercase or lowercase.<br>
 * If only 3 digits are entered, they are expanded to 6 digits by
 * replicating each digit.<br>
 * This syntactical form can represent 16777216 colors.
 * Examples: {@code #9400D3} (i.e. a dark violet), {@code #FFD700} 
 * (i.e. a golden color), {@code #000} (i.e. black) {@code #fff} (i.e. white),
 * {@code #6CF} (i.e. #66CCFF.
 * </li>
 * <li><b>Format.RGB_INTEGER - {@code rrr, ggg, bbb}.</b> Each integer represents one sRGB
 * color component in the order red, green and blue, separated by a comma and
 * optionally by white space. Each integer is in the range 0 to 255.
 * This syntactical form can represent 16777216 colors.
 * Examples: {@code 233, 150, 122} (i.e. a salmon pink), {@code 255, 165, 0}
 * (i.e. an orange).
 * </li>
 * </ul>
 * <p>
 * By default, the formatter formats Color objects with Format.RGB_INTEGER.
 *
 * <p>
 *
 * @author Werner Randelshofer
 * @version $Id: ColorFormatter.java 529 2009-06-08 21:12:23Z rawcoder $
 */
public class ColorFormatter extends DefaultFormatter {

    /**
     * Specifies the formats supported by ColorFormatter.
     */
    public enum Format {

        RGB_HEX,
        RGB_INTEGER
    };
    /**
     * Specifies the preferred output format.
     */
    private Format outputFormat = Format.RGB_INTEGER;
    /**
     * Specifies the last used input format.
     */
    private Format lastUsedInputFormat = null;
    /**
     * This regular expression is used for parsing the RGB_HEX format.
     */
    private final static Pattern rgbHexPattern = Pattern.compile("^\\s*#\\s*([0-9a-fA-F]{3,6})\\s*$");
    /**
     * This regular expression is used for parsing the RGB_HEX format.
     */
    private final static Pattern rgbIntegerPattern = Pattern.compile("^\\s*([0-9]{1,3})\\s*,\\s*([0-9]{1,3}),\\s*([0-9]{1,3})\\s*$");
    /**
     * Specifies whether the formatter allows null values.
     */
    private boolean allowsNullValue = true;
    /**
     * Specifies whether the formatter should adaptively change its output
     * format depending on the last input format used by the user.
     */
    private boolean isAdaptive = true;
    /**
     * Preferences used for storing the last used input format.
     */
    private Preferences prefs;

    public ColorFormatter() {
        this(Format.RGB_INTEGER, true, true);
    }

    public ColorFormatter(Format outputFormat, boolean allowsNullValue, boolean isAdaptive) {
        this.outputFormat = outputFormat;
        this.allowsNullValue = allowsNullValue;
        this.isAdaptive = isAdaptive;

        // Retrieve last used input format from preferences
        prefs = PreferencesUtil.userNodeForPackage(getClass());
        try {
            lastUsedInputFormat = Format.valueOf(prefs.get("ColorFormatter.lastUsedInputFormat", Format.RGB_HEX.name()));
        } catch (IllegalArgumentException e) {
            // leave lastUsedInputFormat as null
        }
        if (isAdaptive && lastUsedInputFormat != null) {
            this.outputFormat = lastUsedInputFormat;
        }

        setOverwriteMode(false);
    }

    /**
     * Sets the output format.
     * @param newValue
     */
    public void setOutputFormat(Format newValue) {
        if (newValue == null) {
            throw new NullPointerException("outputFormat may not be null");
        }
        outputFormat = newValue;
    }

    /**
     * Gets the output format.
     */
    public Format getOutputFormat() {
        return outputFormat;
    }

    /**
     * Gets the last used input format.
     */
    public Format getLastUsedInputFormat() {
        return lastUsedInputFormat;
    }

    /**
     * Sets whether a null value is allowed.
     * @param newValue
     */
    public void setAllowsNullValue(boolean newValue) {
        allowsNullValue = newValue;
    }

    /**
     * Returns true, if null value is allowed.
     */
    public boolean getAllowsNullValue() {
        return allowsNullValue;
    }

    /**
     * Sets whether the color formatter adaptively selects its output
     * format depending on the last input format used by the user.
     *
     * @param newValue
     */
    public void setAdaptive(boolean newValue) {
        isAdaptive = newValue;
        if (newValue && lastUsedInputFormat != null) {
            outputFormat = lastUsedInputFormat;
        }
    }

    /**
     * Returns true, if the color formatter is adaptive.
     */
    public boolean isAdaptive() {
        return isAdaptive;
    }

    private void setLastUsedInputFormat(Format newValue) {
        lastUsedInputFormat = newValue;
        if (isAdaptive) {
            outputFormat = lastUsedInputFormat;
        }
        prefs.put("ColorFormatter.lastUsedInputFormat", newValue.name());
    }

    @Override
    public Object stringToValue(String str) throws ParseException {

        // Handle null and empty case
        if (str == null || str.trim().length()==0) {
            if (allowsNullValue) {
                return null;
            } else {
                throw new ParseException("Null value is not allowed.", 0);
            }
        }

        // Format RGB_HEX
        Matcher matcher = rgbHexPattern.matcher(str);
        if (matcher.matches()) {
            setLastUsedInputFormat(Format.RGB_HEX);
            try {
                String group1 = matcher.group(1);
                if (group1.length() == 3) {
                    return new Color(Integer.parseInt(
                            "" + group1.charAt(0) + group1.charAt(0) + //
                            group1.charAt(1) + group1.charAt(1) + //
                            group1.charAt(2) + group1.charAt(2), //
                            16));
                } else if (group1.length() == 6) {
                    return new Color(Integer.parseInt(group1, 16));
                } else {
                    throw new ParseException("Hex color must have 3 or 6 digits.", 1);
                }
            } catch (NumberFormatException nfe) {
                ParseException pe = new ParseException(str, 0);
                pe.initCause(nfe);
                throw pe;
            }
        }

        // Format RGB_INTEGER
        matcher = rgbIntegerPattern.matcher(str);
        if (matcher.matches()) {
            setLastUsedInputFormat(Format.RGB_INTEGER);
            try {
                return new Color(//
                        Integer.parseInt(matcher.group(1)), //
                        Integer.parseInt(matcher.group(2)), //
                        Integer.parseInt(matcher.group(3)));
            } catch (NumberFormatException nfe) {
                ParseException pe = new ParseException(str, 0);
                pe.initCause(nfe);
                throw pe;
            } catch (IllegalArgumentException iae) {
                ParseException pe = new ParseException(str, 0);
                pe.initCause(iae);
                throw pe;
            }
        }

        throw new ParseException(str, 0);
    }

    @Override
    public String valueToString(Object value) throws ParseException {
        String str = null;

        if (value == null) {
            if (allowsNullValue) {
                str = "";
            } else {
                throw new ParseException("Null value is not allowed.", 0);
            }
        } else {
            if (!(value instanceof Color)) {
                throw new ParseException("Value is not a color " + value, 0);
            }

            Color c = (Color) value;

            switch (outputFormat) {
                case RGB_HEX:
                    str = "000000" + Integer.toHexString(c.getRGB() & 0xffffff);
                    str = "#" + str.substring(str.length() - 6);
                    break;
                case RGB_INTEGER:
                    str = c.getRed() + "," + c.getGreen() + "," + c.getBlue();
                    break;
            }
        }
        return str;
    }

    /**
     * Convenience method for creating a formatter factory with a
     * {@code ColorFormatter}.
     * Uses the RGB_INTEGER format, allows null values and is adaptive.
     */
    public static AbstractFormatterFactory createFormatterFactory() {
        return createFormatterFactory(Format.RGB_INTEGER, true, true);
    }

    /**
     * Convenience method for creating a formatter factory with a
     * 8@code ColorFormatter}.
     */
    public static AbstractFormatterFactory createFormatterFactory(Format outputFormat, boolean allowsNullValue, boolean isAdaptive) {
        return new DefaultFormatterFactory(new ColorFormatter(outputFormat, allowsNullValue, isAdaptive));
    }
}
