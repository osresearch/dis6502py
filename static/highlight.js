function get_anchor(url) { return url.split("#")[1] }
function highlight(url, enable)
{
	var anchor = url.split("#")[1];
	if (!anchor) return;
	var dest = document.getElementById(anchor);
	if (!dest) return;
	console.log("focus", anchor, dest, enable)
	if (enable)
		dest.classList.add("highlight");
	else
		dest.classList.remove("highlight");
}

for(var el of document.getElementsByClassName("link"))
{
	el.addEventListener("mouseenter", (event) => highlight(event.target.href, true));
	el.addEventListener("mouseleave", (event) => highlight(event.target.href, false));
}
