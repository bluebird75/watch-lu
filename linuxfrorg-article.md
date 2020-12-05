Combien d'utilisateurs pour LuaUnit ?



Cher Journal. 

Dans des aventures précédentes, je t'ai raconté comment [GitHub avait ressuscité le moribond *LuaUnit*](https://linuxfr.org/users/bluebird/journaux/comment-github-a-ressuscite-mon-logiciel-libre) et comment [le packaging de *LuaUnit* faisait une sacrée différence](https://linuxfr.org/users/bluebird/journaux/a-propos-de-packaging-et-de-luaunit) en terme de popularité d'un logiciel.

Je t'avais promis des statistiques détaillées et je sais que tu n'en pouvais plus d'attendre. Soit rassuré! Le jour est arrivé où tu sauras tout sur la popularité de [LuaUnit](https://github.com/bluebird75/luaunit) ! Et peut-être en apprendras-tu un peu plus sur la popularité générale des logiciels libres.


Chez LuaRocks
=============

Pour ceux qui ne connaissent pas [LuaUnit](https://github.com/bluebird75/luaunit), il s'agit d'une bibliothèque pour le langage *Lua* permettant d'écrire et exécuter facilement des tests unitaires. C'est dans le même esprit que *unittest* en Python ou *JUnit* en Java.

J'ai écrit LuaUnit en 2004. Le projet a connu des hauts et des bas [que je raconte dans mon précédent journal](https://linuxfr.org/users/bluebird/journaux/comment-github-a-ressuscite-mon-logiciel-libre). En 2016, un évènement important eût lieu: je fournis pour la première fois une version packagée de LuaUnit. Dans le monde Lua, cela veut dire fournir un *Rock* pour le gestionnaire de paquetage [LuaRocks](https://luarocks.org/).


*LuaRocks* a la gentillesse de décompter le nombre de téléchargements [sur la page du package](https://luarocks.org/modules/bluebird75/luaunit). Et là, au bout de quelques jours, le clavier m'en tombe des mains! LuaUnit est téléchargé à un rythme de 100 installations par jour. Te rends-tu compte cher journal ? Une centaine de nouveaux utilisateurs par jour! Et le rythme va même monter jusqu'à 600 téléchargements par jour! A l'heure où j'écris ces lignes, **LuaUnit a été téléchargée en tout 385 781 fois** . Pour un projet aussi modeste, ces chiffres sont tout simplement vertigineux!

Je rappelle que Lua est un langage relativement confidentiel, et que LuaUnit n'est pas la seule bibliothèque de test unitaire.

Dès les premiers jours, je me suis posé la question de la durabilité de cette tendance. Pour avoir une réponse claire, j'ai pris mon Python favori, la bibliothèque de web scraping [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) et j'ai scrapé le nombre de téléchargements sur la page LuaRocks. J'ai ensuite glissé le résultat dans un fichier texte que je conserve sous Git, et j'ai entouré tout ça d'un cron journalier pour ne rien perdre de l'histoire.

Voici ce que cela donne aujourd'hui sous forme d'un beau graphique:


[graphique 1]

Note: la moyenne est calculé sous forme de moyenne mobile exponentielle (avec alpha = 0.1, cf [[Moyenne mobile]] sur Wikipedia)


Comme vous le voyez, ça télécharge à un sacré rythme! J'ai longtemps été sceptique sur le fait que ce nombre de téléchargement corresponde réellement à des nouveaux utilisateurs, sans pour autant trouver une bonne explication. C'est [jylog](https://linuxfr.org/users/bluebird/journaux/a-propos-de-packaging-et-de-luaunit#comment-1798379) qui me l'a soufflée dans mon précédent journal: LuaUnit est maintenant utilisé en intégration continue, et donc téléchargé à chaque *build* et très probablement à chaque *commit* d'un projet. Ça explique un peu la croissance régulière mais tout de même, quand on monte à 600 téléchargements par jour, ça fait soit un sacré gros projet qui utilise LuaUnit, soit un sacré paquet de petits projets (et très probablement l'ensemble des deux).

Ce qui saute aux yeux dans le graphique de la moyenne, c'est la période *novembre 2016* à *août 2017* où le rythme de téléchargement journalier passe de 200 à 600. Du côté de LuaUnit, cela ne correspond à rien de particulier. Il s'agit probablement d'un très gros projet qui a utilisé LuaUnit pendant un an en intégration continue. Avec 400 build par jour, on est pas chez des amateurs en tout cas.

En dehors de cette période exceptionnelle la moyenne décroit lentement; cela correspond probablement au scenario suivant: les projets Lua existants qui avaient besoin de LuaUnit l'ont installé durant les deux premières années. Les téléchargements suivants sont alimentés par l'intégration continue et par les nouveaux projets démarrant sous Lua, nécessairement moins nombreux que la base existante.

Depuis juillet 2020, on voit que le nombre de téléchargement repart à la hausse. C'est très probablement une conséquence d'un évènement majeur dans le monde Lua: la sortie de Lua 5.4 . Pas mal de projet en CI ont du rajouter un build spécifique Lua 5.4 (comme je l'ai fait) et générer plein de nouveaux téléchargements.

Au final, ces chiffres de téléchargements sont quand même très difficiles à interpréter. Je suis un peu déçu. Rapidement, je me suis tourné vers une autre métrique que je vous présente tout de suite.



Chez GitHub
============================

On ne présente plus [GitHub](https://www.github.com) la plate-forme d'hébergement de projets. Sympathiquement, GitHub fournit un [service de recherche de code](https://docs.github.com/en/free-pro-team@latest/github/searching-for-information-on-github/searching-code). Il est donc possible de chercher le nombre de projet hébergés sur GitHub qui utilisent LuaUnit. Là, je tiens une mesure fiable! (enfin, c'est ce que je croyais).

Le service est accessible via [une API REST bien pratique](https://docs.github.com/en/free-pro-team@latest/rest/reference/search#search-code) (même si j'ai commencé à l'utiliser avec du web scraping). J'ai donc étoffé mon cron journalier de suivi de popularité avec un appel à GitHub concernant le nombre de projets utilisant LuaUnit.

En rédigeant ce journal, je me suis dit que j'allais vérifier la fiabilité des résultats avant de vous parler des 5500 projets que j'ai trouvé. Et là, petite déception, ma requête était mal formulée; elle retournait beaucoup de faux positifs. Je l'avais bricolée vite fait le jour où je l'ai créée. Elle cherchait tous les projets avec la chaîne `luaunit.lua`. Sauf qu'en lisant la [documentation de GitHub Search], j'ai découvert que le `.` est ignoré, et que je cherchais en fait tous les fichiers qui contiennent les deux mots `luaunit` et `lua`. Or il existe plusieurs moteurs de jeu ou de scripting avec une interface Lua qui décrivent des unités de jeu avec une classe nommée... LuaUnit. Oups ! Je suis aussi tombé sur de la documentation de LuaUnit que d'autres projets ont inclus directement.

J'ai donc affiné ma requête en ne cherchant que dans les fichiers lua, les deux mot-clés spécifiques `require` et `luaunit`. C'est comme ça qu'on importe un fichier en Lua. J'aurai aimé faire plus fin en cherchant `require('luaunit')` mais je serai passé à côté de pas mal de résultats. En effet, en Lua les syntaxes suivantes sont parfaitement équivalentes:

	require("luaunit") 
	require('luaunit') 
	require 'luaunit' 
	require "luaunit" 


C'est une des nombreuses particularités du langage Lua, les parenthèses d'un appel de fonction sont optionelles dans certains cas.

Un autre aspect que j'avais complètement négligé dans ma requête initiale est que je veux compter le nombre de projets utilisant LuaUnit, mais que je compte en fait le nombre d’occurrences de code `LuaUnit` dans GitHub, avec possiblement plusieurs résultats par projets (que GitHub limite tout de même à deux). Un autre facteur d'erreur est que un projet avec plusieurs utilisateurs aura plusieurs clone sur GitHub et retournera un hit pour chacun de ces clones. J'ai donc affiné mon script en examinant l'ensemble des résultats retournés et en ne comptant que les noms de projets uniques. J'ai rencontré cependant une autre limitation: GitHub ne me laisse examiner que les 1000 premiers résultats de ma recherche. Pas grave, je calcule le ratio `nombre de projets / nombre de résultats` sur les 1000 premiers résultats et je l'applique sur sur le nombre de résultats de ma recherche.

Avec ces ajustements, on passe de 5500 résultats à 1172 projets effectifs. Par contre, cette fois, c'est du solide. J'ai appliqué rétroactivement le ratio `1172 / 5500` aux chiffres que j'avais stocké afin de présenter une courbe réaliste.

Une autre question qui m'intéresse est de savoir combien de nouveaux projets utilisent LuaUnit. Pour avoir un rendu un peu régulier, j'ai accumulé ce résultat par trimestre et ça donne la courbe que vous voyez ci-dessous.

[graphics 2]

On constate une courbe de croissance assez régulière du nombre de projet total. Je suis content dès que j'ai un utilisateur. Alors 1200, imaginez comment c'est bon pour le moral ! Au niveau des nouveaux projets, on est aux alentours de 40 nouveaux projets par trimestre qui décident d'utiliser LuaUnit. Pareil, ça fait chaud au cœur. J'aurai pas imaginé que Lua et LuaUnit puissent être aussi populaire en 2020!



Packaging ou Vendoring ?
========================

Pour ceux qui ne connaissent pas les termes, c'est une description de la façon de gérer une dépendance externe dans un projet:

* en mode *packaging*, on déclare la dépendance au gestionnaire de paquet et on s'appuie sur ce dernier pour en réaliser l'installation
* en mode *vendoring*, on inclut directement les sources du logiciel dont on dépend dans le projet.

Ces dernières années, le vendoring est plutôt passé de mode, le packaging ayant largement pris le pas en terme de pratique.

Du côté de LuaUnit, avant juillet 2016, la seule façon de l'installer était en mode vendoring, en copiant le fichier `luaunit.lua` dans le projet. C'est une méthode simple et fiable, qui remonte à une époque où il n'y avait pas d'outil de packaging pour Lua. J'ai tardé à fournir un paquet installable pour LuaUnit, à tort comme je l'explique dans mon journal car visiblement, cela permet de toucher un nombre vraiment important d'utilisateurs. Mais en 2016, j'ai fait le pas. Je suis curieux de savoir si parmi mes utilisateurs le vendoring existe toujours, ou si le packaging a tout écrasé. Encore une fois, l'API de recherche de code de GitHub est mon amie: je peux lancer une requête de recherche sur tous les projets qui contiennent un fichier `luaunit.lua`. Cette fois, pas de faux positifs!

Ça donne le graphique ci-dessous:


[graphics 3]

Sans surprise, on voit que le packaging est dominant dans l'utilisation de LuaUnit, et que cette proportion s'accroit doucement. Mais, on voit aussi que la courbe du vendoring ne stagne pas. Il y a des nouveaux projets sous Lua qui démarrent et incluent directement LuaUnit dans leurs sources. Je vais donc garder la facilité d'installation de LuaUnit en mode vendoring, c'est à dire de tout mettre dans un seul fichier. Habituellement, j'aime pas tellement les fichiers de 3000 lignes rassemblant des trucs qui n'ont rien à voir ensemble, mais si c'est pour simplifier la vie des utilisateurs, je n'hésite pas.



Une star chez GitHub
=====================

GitHub fournit un autre indice de la popularité d'un projet: les utilisateurs peuvent vous décerner des étoiles. On peut aussi compter le nombre de fork et de suiveurs. Note amusante, j'ai toujours eu le même nombre de suiveurs que d'étoiles. Cela signifie que tous ceux qui m'ont décerné une étoile me suivent sur GitHub. Perso, j'ai souvent donné des étoiles à des projets que j'aime bien sans les suivre pour autant; je semble être atypique dans mon utilisation de GitHub. 

Comme vous vous en doutez à ce stade de l'article, j'ai suivi l'historique du nombre d'étoiles de mon projet. Ce qui me parait intéressant, c'est de le comparer au nombre d'utilisateur et de répondre à cette question fondamentale: combien d'utilisateurs réels pour une étoile décernée ? Sachant que la réponse est potentiellement généralisable à d'autres projets sous GitHub.

Pour calculer le nombre d'utilisateur, je suis reparti de la requête qui me donne le nombre de hit pour une recherche sur `require`+`luaunit` et j'ai compté cette fois toutes les paires (utilisateurs, projet). Pour les étoiles, je me suis servi de l'API REST de base de GitHub.

Voici ce que ça donne:

[graphics 4]

Sans surprise, on a une croissance régulière des deux courbes. Par contre, je suis estomaqué par le ratio que j'obtiens: un utilisateur sur quatre décernerai une étoile au projet. Ça me parait incroyablement élevé. On peut modérer cela par le fait que je ne capture certainement pas tous les utilisateurs mais tout de même. Ça indiquerai une propension généreuse à distribuer des étoiles.



Conclusion
==========

Voilà, vous savez tout sur la popularité de LuaUnit. Si j'ai fait une erreur de méthodologie, n'hésitez pas m'en faire part. Si vous avez d'autres idées pour mesurer la popularité de LuaUnit ou d'un logiciel en général, je suis également preneur. J'aurai bien aimé faire des recherches similaires sur GitLab mais ils n'ont pas d'API de recherche de code aussi pratique à utiliser. Si vous aussi, vous traquez la popularité de votre logiciel libre comme un maniaque, mettez un commentaire, je me sentirai moins seul!

Cet article était aussi une excuse pour apprendre à faire des graphes sur [matplotLib](https://matplotlib.org/). Je confirme sa réputation, c'est vraiment facile à utiliser et bien documenté.

Les chiffres utilisés comme source pour cet article sont disponibles dans ce fichier: [dbdict.txt](https://github.com/bluebird75/watch-lu/blob/master/dbdict.txt) . J'utilise un simple format texte (en fait un dictionnaire Python), j'envisage de convertir ça un jour en *JSON* pour faire moderne.

Mon script qui recueille les résultats toutes les nuits est là: [watch_luaunit.py](https://github.com/bluebird75/watch-lu/blob/master/watch_luaunit.py) . Attention, ça reste un truc fait à l'arrache.

La digestion des données et génération des graphes matplotlib est faite ici: [plot-lu.py](https://github.com/bluebird75/watch-lu/blob/master/plot-lu.py)

Une prochaine fois, je vous parlerai peut-être de ce que mes utilisateurs m'ont apporté comme contribution.











