<%!
	section = "docs"
%>
<%inherit file="_templates/i3.mako" />
<div id="content" class="usergen">
<h1>User-contributed article: enhanced and extensible i3bar with py3status</h1>

<p>
In the i3 documentation, the recommended tool for <a
href="http://i3wm.org/docs/userguide.html#_displaying_a_status_line">displaying
a status line is to use i3status</a> combined with i3bar.
</p>

<p>
While i3status is very efficient at what it does, it is by design limited to
a few modules and does not allow you to inject your own scripts output on your
i3bar. This is said pretty clearly on the i3status man page:
</p>

<pre><tt>In i3status, we don’t want to implement process management again.
Therefore, there is no module to run arbitrary scripts or commands.
Instead, you should use your shell.</tt></pre>

<h2>Introducing py3status</h2>

<p>
The goal of py3status is to fill this gap by allowing users to simply extend
their i3bar while preserving their current i3status configuration. The main idea
is to rely on i3status' strenghts without adding any configuration on the user's
side. py3status is thus a wrapper script for i3status and you can
<a href="https://github.com/ultrabug/py3status/wiki"> read more on the wiki</a>.
</p>

<h2>Requirements</h2>

<p>
To acheive this, py3status uses the <a
href="http://i3wm.org/docs/i3bar-protocol.html">i3bar protocol</a> so your
i3status.conf should specify this as its output_format.
</p>

<pre><tt>general {
    output_format = "i3bar"
}</tt></pre>

<h2>Usage</h2>

<p>
Using py3status is easy, no need to multi-pipe your scripts after i3status.
Instead, just replace i3status in your current status_command by py3status.
For example, if you're using your own i3status.conf, you need to change your
i3 config file with:
</p>

<pre><tt>status_command py3status -c ~/.i3/i3status.conf</tt></pre>

<h2>Display your own stuff</h2>

<p>
py3status features a simple and straightfoward plugin system which you can use
to get your own output displayed on your i3bar. You can read more and view some
examples <a
href="https://github.com/ultrabug/py3status/wiki/Write-your-own-modules"> on the
wiki</a>.
</p>

<h2>Documentation</h2>

<p>
You can read the full and up to date documentation on the <a
href="https://github.com/ultrabug/py3status">py3status home page</a>.
</p>
