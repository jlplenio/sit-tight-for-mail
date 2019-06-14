#######################
Sit Tight For Mail
#######################

Small library to crawl websites, save the results in a SQL database and notify users per email.

Capable of handling multiple separate user specific links and keyword searches.

Currently works with:


* `www.immobilienscout24.de <https://www.immobilienscout24.de>`_
    - craws and saves all flats in provided link, capable of handling multiple links and requests
    - email notification per new flat
    - use: respond/apply faster to flat offering

* `www.mydealz.de <https://www.mydealz.de>`_
    - craws and saves all news deals
    - email notification on keyword hit
    - use: track bargains, respond faster to (buy) bargains

******************************
JSON config examples
******************************
www.mydealz.de

.. code-block:: javascript

    {
      "search1": {
        "email": "recipient@mail.com",
        "keywords": ["Cat", "Dog", "Toy","Tesla"]
      },
      "search2": {},
      "search3": {}
    }



www.immobilienscout24.de

.. code-block:: javascript

    {
      "search1": {
        "email": "email@gmail.com",
        "link": "https://www.immobilienscout24.de/Suche/S-2/Wohnung-Miete/Berlin/Berlin/-/1,00-1,00/-/-/-/-/true"
      },

      "search2": {},
      "search3": {}
    }




***************
Requirements
***************

* Beautiful Soup
* requests
* pymysql

- mailbox with encrypted SMTP access
- MySQL server

